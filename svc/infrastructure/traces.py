import contextvars

import opentelemetry.trace as trace
from fastapi import FastAPI
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import format_trace_id

from svc.persist.database import database
from svc.settings import TracingSettings

trace_id_context_var = contextvars.ContextVar("trace_id", default="")


def set_trace_context_var(span: trace.Span, scope: dict) -> None:
    trace_id_context_var.set(format_trace_id(span.get_span_context().trace_id))


def configure_traces(app: FastAPI, settings: TracingSettings) -> None:
    tracer_provider = TracerProvider(
        sampler=ParentBasedTraceIdRatio(settings.sampling_rate),
        resource=Resource.create(
            {
                SERVICE_NAME: "promotion-service",
                SERVICE_NAMESPACE: "b2c",
                SERVICE_VERSION: "unknown",
            }
        ),
    )
    trace.set_tracer_provider(tracer_provider)

    if settings.jaeger_enabled:
        jaeger_exporter = JaegerExporter(
            agent_host_name=settings.jaeger_agent_host_name,
            agent_port=settings.jaeger_agent_port,
            collector_endpoint=settings.jaeger_collector_endpoint,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    if settings.zipkin_enabled:
        zipkin_exporter = ZipkinExporter(endpoint=settings.zipkin_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))
    if settings.console_enabled:
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    set_global_textmap(B3MultiFormat())

    FastAPIInstrumentor.instrument_app(
        app,
        server_request_hook=set_trace_context_var,
        excluded_urls="/health,/metrics",
    )
    SQLAlchemyInstrumentor().instrument(engine=database.engine.sync_engine)
