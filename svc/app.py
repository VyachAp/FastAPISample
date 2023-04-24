from customer_profile.api_client.client import CustomerProfileClient
from fastapi import FastAPI
from warehouse.api_client.client import WarehouseGeneralClient

from svc.api.errors.handlers import register_exception_handlers
from svc.events.consumer import create_consumer
from svc.infrastructure.catalog.client import CatalogClient
from svc.infrastructure.logging import configure_logging
from svc.infrastructure.metrics import configure_metrics, errors_counter
from svc.infrastructure.traces import configure_traces
from svc.persist.database import database
from svc.router import prepare_router
from svc.settings import get_service_settings


async def on_startup() -> None:
    await database.startup()


async def on_shutdown() -> None:
    await database.shutdown()


def create_app() -> FastAPI:
    settings = get_service_settings()
    configure_logging(settings.logging_profile)

    consumer = create_consumer(settings, database)
    warehouse_client = WarehouseGeneralClient.instance()
    customer_client = CustomerProfileClient.instance()
    catalog_client = CatalogClient.instance()

    app = FastAPI(
        title="Promotion Service",
        version="0.0.0",
        on_startup=[
            on_startup,
            consumer.start,
        ],
        on_shutdown=[
            on_shutdown,
            consumer.stop,
            warehouse_client.shutdown,
            customer_client.shutdown,
            catalog_client.shutdown,
        ],
    )

    prepare_router(app.router)

    configure_traces(app, settings.tracing)
    configure_metrics(app)

    register_exception_handlers(app, errors_counter)

    return app
