import asyncio
import uuid
from os import environ
from typing import AsyncIterator, Iterator
from unittest.mock import Mock

import alembic.config
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pricing.api_client.client import PricingClient
from pricing.models.base import PricingApiResponse, PricingListResult
from pricing.models.v2.prices import ProductPriceV2ListRequest, ProductPriceV2Model
from pytest_mock import MockerFixture
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from warehouse.api_client.client import WarehouseGeneralClient
from warehouse.models.base_model import ApiResponse as WarehouseApiResponse
from warehouse.models.warehouse import Location, Polygon, WarehouseModel

from svc.app import create_app
from svc.persist import schemas
from svc.persist.database import conditions_database, Database, database
from svc.persist.schemas.metadata import PublicSchema
from svc.utils.module_loader import import_submodules
from tests import factories
from tests.factories.base_factory import AsyncFactory


@pytest.fixture(scope="session")
def event_loop(request: pytest.FixtureRequest) -> Iterator[asyncio.AbstractEventLoop]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db() -> AsyncIterator[Database]:
    await database.startup()
    yield database
    await database.shutdown()


@pytest.fixture(scope="session")
async def conditions_db() -> AsyncIterator[Database]:
    async with conditions_database.engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public"))

    alembic.config.main(
        argv=[
            "--raiseerr",
            "upgrade",
            "head",
        ]
    )
    yield conditions_database
    await conditions_database.shutdown()


conditions_db_tables = {
    "warehouse_bonus_settings",
    "warehouse_fees",
    "fees",
    "user_fees",
    "warehouse_happy_hours",
    "warehouse_forced_happy_hours",
    "warehouse_happy_hours_settings",
}


@pytest.fixture(autouse=True)
async def db_connection(app: FastAPI, db: Database) -> AsyncIterator[AsyncConnection]:
    async with database.engine.begin() as trn:
        for cls in get_schemas():
            if cls.__table__ in conditions_db_tables:
                continue

            await trn.execute(text(f"TRUNCATE {cls.__table__} RESTART IDENTITY CASCADE;"))

    async with db.engine.connect() as conn:

        async def get_conn() -> AsyncConnection:
            return conn

        app.dependency_overrides[db.connection] = get_conn
        yield conn


@pytest.fixture(autouse=True)
async def conditions_db_connection(app: FastAPI, conditions_db: Database) -> AsyncIterator[AsyncConnection]:
    async with conditions_db.engine.begin() as trn:
        for cls in get_schemas():
            if cls.__table__ in conditions_db_tables:
                await trn.execute(text(f"TRUNCATE {cls.__table__} RESTART IDENTITY CASCADE;"))

    async with conditions_db.engine.connect() as conn:

        async def get_conn() -> AsyncConnection:
            return conn

        app.dependency_overrides[conditions_db.connection] = get_conn
        yield conn


@pytest.fixture(scope="session")
async def app(db: Database) -> FastAPI:
    environ["services_warehouse_url"] = "http://test"
    environ["services_customer_profile_url"] = ""
    environ["services_catalog_url"] = ""
    environ["services_pricing_url"] = ""
    application = create_app()

    return application


@pytest.fixture(scope="session")
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def prepare_factories(db_connection: AsyncConnection) -> None:
    for factory in get_factories():
        if factory._meta.model and factory._meta.model.__table__ not in conditions_db_tables:
            factory._meta.connection = db_connection


@pytest.fixture(autouse=True)
def prepare_conditions_factories(conditions_db_connection: AsyncConnection) -> None:
    for factory in get_factories():
        if factory._meta.model and factory._meta.model.__table__ in conditions_db_tables:
            factory._meta.connection = conditions_db_connection


def get_factories() -> Iterator[type[AsyncFactory]]:
    for module in import_submodules(factories.__name__).values():
        yield from (cls for cls in module.__dict__.values() if isinstance(cls, type) and issubclass(cls, AsyncFactory))


def get_schemas() -> Iterator[PublicSchema]:
    enum_tables = list[PublicSchema]()
    for module in import_submodules(schemas.__name__).values():
        yield from (
            cls
            for cls in module.__dict__.values()
            if isinstance(cls, type) and type(cls) is PublicSchema and cls not in enum_tables
        )


@pytest.fixture(autouse=True)
async def mock_pricing_get_empty_prices(mocker) -> Mock:
    async def get_product_prices_cents(*args, **kwargs) -> PricingApiResponse[PricingListResult[ProductPriceV2Model]]:
        return PricingApiResponse[PricingListResult[ProductPriceV2Model]](
            result=PricingListResult[ProductPriceV2Model](items=[])
        )

    return mocker.patch.object(
        PricingClient.instance(), PricingClient.get_product_prices_cents.__name__, wraps=get_product_prices_cents
    )


@pytest.fixture()
async def mock_pricing_get_prices_with_items_purchase(mocker) -> Mock:
    async def get_product_prices_cents(
        request: ProductPriceV2ListRequest,
    ) -> PricingApiResponse[PricingListResult[ProductPriceV2Model]]:
        return PricingApiResponse[PricingListResult[ProductPriceV2Model]](
            result=PricingListResult[ProductPriceV2Model](
                items=[
                    ProductPriceV2Model(
                        product_id=it,
                        purchase_price=50,
                        selling_price=100,
                        discounted_price=100,
                    )
                    for it in request.product_ids
                ]
            )
        )

    return mocker.patch.object(
        PricingClient.instance(), PricingClient.get_product_prices_cents.__name__, wraps=get_product_prices_cents
    )


@pytest.fixture
def get_warehouse_mocked(mocker: MockerFixture) -> None:
    async def get_warehouse(warehouse_id: uuid.UUID) -> WarehouseApiResponse[WarehouseModel]:
        return WarehouseApiResponse[WarehouseModel](
            result=WarehouseModel(
                id=warehouse_id,
                name="name",
                address="address",
                location=Location(
                    type="point",
                    coordinates=[],
                ),
                active=True,
                tz="America/Chicago",
                coverage=Polygon(
                    type="polygon",
                    coordinates=[
                        [],
                    ],
                ),
                is_supermarket_zone_enabled=False,
            )
        )

    mocker.patch.object(
        WarehouseGeneralClient.instance().warehouse,
        WarehouseGeneralClient.instance().warehouse.get_warehouse.__name__,
        wraps=get_warehouse,
    )
