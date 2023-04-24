import re
import typing

import opentelemetry.trace as trace
from opentelemetry.context.context import Context
from opentelemetry.propagators.textmap import CarrierT, Getter, Setter, TextMapPropagator
from opentelemetry.trace import format_span_id, format_trace_id


class KafkaHeadersGetter(Getter):
    def get(self, carrier: typing.Sequence[tuple[str, bytes]], key: str) -> typing.Optional[typing.List[str]]:
        return [v.decode("utf-8") for (k, v) in carrier if k == key]

    def keys(self, carrier: typing.Sequence[tuple[str, bytes]]) -> typing.List[str]:
        return [k for (k, v) in carrier]


class KafkaHeadersSetter(Setter):
    def set(
        self,
        carrier: typing.List[typing.Tuple[str, bytes]],
        key: str,
        value: str,
    ) -> None:
        """Setter implementation to set a value into a kafka message headers.

        Args:
            carrier: list in which to set value
            key: the key used to set the value
            value: the value to set
        """
        carrier.append((key, value.encode("utf-8")))


kafka_getter = KafkaHeadersGetter()
kafka_setter = KafkaHeadersSetter()


class KafkaTraceFormat(TextMapPropagator):
    TRACE_ID_KEY = "trace_id"
    SAMPLED_KEY = "sampled"
    SPAN_ID_KEY = "span_id"
    FLAGS_KEY = "flags"
    _SAMPLE_PROPAGATE_VALUES = {"1", "True", "true", "d"}
    _trace_id_regex = re.compile(r"[\da-fA-F]{16}|[\da-fA-F]{32}")
    _span_id_regex = re.compile(r"[\da-fA-F]{16}")

    def extract(
        self,
        carrier: CarrierT,
        context: typing.Optional[Context] = None,
        getter: Getter = kafka_getter,
    ) -> Context:
        if context is None:
            context = Context()

        trace_id = _extract_first_element(getter.get(carrier, self.TRACE_ID_KEY))
        span_id = _extract_first_element(getter.get(carrier, self.SPAN_ID_KEY))
        sampled = _extract_first_element(getter.get(carrier, self.SAMPLED_KEY)) or "0"
        flags = _extract_first_element(getter.get(carrier, self.FLAGS_KEY)) or None

        if (
            trace_id is None
            or span_id is None
            or self._trace_id_regex.fullmatch(trace_id) is None
            or self._span_id_regex.fullmatch(span_id) is None
        ):
            return context

        options = 0
        if sampled in self._SAMPLE_PROPAGATE_VALUES or flags == "1":
            options |= trace.TraceFlags.SAMPLED

        return trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    # trace an span ids are encoded in hex, so must be converted
                    trace_id=int(trace_id, base=16),
                    span_id=int(span_id, base=16),
                    is_remote=True,
                    trace_flags=trace.TraceFlags(options),
                    trace_state=trace.TraceState(),
                )
            ),
            context,
        )

    def inject(
        self,
        carrier: CarrierT,
        context: typing.Optional[Context] = None,
        setter: Setter = kafka_setter,
    ) -> None:
        span = trace.get_current_span(context=context)

        span_context = span.get_span_context()
        if span_context == trace.INVALID_SPAN_CONTEXT:
            return

        sampled = (trace.TraceFlags.SAMPLED & span_context.trace_flags) != 0
        setter.set(
            carrier,
            self.TRACE_ID_KEY,
            format_trace_id(span_context.trace_id),
        )
        setter.set(carrier, self.SPAN_ID_KEY, format_span_id(span_context.span_id))
        setter.set(carrier, self.SAMPLED_KEY, "1" if sampled else "0")

    @property
    def fields(self) -> typing.Set[str]:
        return {
            self.TRACE_ID_KEY,
            self.SPAN_ID_KEY,
            self.SAMPLED_KEY,
        }


def _extract_first_element(
    items: typing.Optional[typing.Iterable[CarrierT]],
) -> typing.Optional[CarrierT]:
    if items is None:
        return None

    return next(iter(items), None)


kafka_trace_formatter = KafkaTraceFormat()
