from fastapi import FastAPI
from prometheus_client import Counter
from starlette_exporter import PrometheusMiddleware, handle_metrics

errors_counter = Counter(
    "business_errors_count",
    "Count for business error at API",
    labelnames=["app_name", "error_code"],
)

METRICS_PATH = "/metrics"
HEALTH_PATH = "/health"


def configure_metrics(app: FastAPI) -> None:
    app.add_middleware(
        PrometheusMiddleware,
        app_name="promotion-service",
        group_paths=True,
        skip_paths=[METRICS_PATH, HEALTH_PATH],
    )
    app.add_route(METRICS_PATH, handle_metrics)
