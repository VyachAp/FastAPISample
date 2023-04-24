from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from customer_profile.api.models.user import UserListFilter
from customer_profile.api_client.client import CustomerProfileClient
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncConnection
from warehouse.api_client.warehouse import WarehouseClient
from warehouse.models.warehouse import WarehouseListFilters

from svc.api.models.base_model import ApiResponse
from svc.api.models.bulk import (
    BulkCouponModel,
    BulkCouponRequest,
    BulkCouponValueModel,
    BulkCouponValueRequest,
    BulkOperation,
    BulkResponse,
    CategoriesNotFoundError,
    DuplicatedItemError,
    UsersNotFoundError,
    WarehousesNotFoundError,
)
from svc.api.models.coupon import CouponKind
from svc.infrastructure.catalog.client import CatalogClient
from svc.infrastructure.catalog.models import CategoryListRequest
from svc.services.coupon.dto import CouponModel
from svc.utils.money import cents_to_dollars, dollars_to_cents
from tests.factories.coupon import CouponFactory
from tests.helpers import get_coupon


class FakeObject:
    def __init__(self, data: dict) -> None:
        for k, v in data.items():
            if isinstance(v, dict):
                v = FakeObject(v)

            if isinstance(v, list):
                fake_list = list()
                for item in v:
                    if isinstance(item, dict):
                        item = FakeObject(item)
                    fake_list.append(item)
                v = fake_list

            self.__dict__[k] = v


def mock_clients(
    mocker: MockerFixture,
    wrong_warehouses: list[UUID] | None = None,
    wrong_categories: list[UUID] | None = None,
    wrong_users: list[UUID] | None = None,
) -> None:
    async def get_warehouses(client: Any, filters_request: WarehouseListFilters) -> FakeObject:
        items = list[dict]()
        if filters_request.warehouse_ids:
            items.extend(
                {"id": warehouse_id}
                for warehouse_id in filters_request.warehouse_ids
                if warehouse_id not in (wrong_warehouses or [])
            )

        return FakeObject(
            {
                "result": {"items": items},
                "error": None,
            }
        )

    async def get_categories(client: Any, request: CategoryListRequest) -> FakeObject:
        items = list[dict]()
        if request.category_ids:
            items.extend(
                {"id": category_id}
                for category_id in request.category_ids
                if category_id not in (wrong_categories or [])
            )
        return FakeObject(
            {
                "result": {"items": items},
                "error": None,
            }
        )

    async def get_customers(client: Any, filters: UserListFilter) -> FakeObject:
        items = list[dict]()
        if filters.user_ids:
            items.extend({"id": user_id} for user_id in filters.user_ids if user_id not in (wrong_users or []))
        return FakeObject(
            {
                "result": {"items": items},
                "error": None,
            }
        )

    mocker.patch.object(
        WarehouseClient,
        WarehouseClient.list_warehouses.__name__,
        autospec=True,
        side_effect=get_warehouses,
    )

    mocker.patch.object(
        CatalogClient,
        CatalogClient.get_categories.__name__,
        autospec=True,
        side_effect=get_categories,
    )
    mocker.patch.object(
        CustomerProfileClient,
        CustomerProfileClient.search_users.__name__,
        autospec=True,
        side_effect=get_customers,
    )


def calculate_value(value: Decimal, kind: CouponKind) -> int:
    if kind == CouponKind.fixed:
        return int(value)

    return dollars_to_cents(value)


def assert_is_equal(bulk_item: BulkCouponModel, coupon: CouponModel) -> None:

    assert bulk_item.name.lower() == coupon.name.lower()
    assert bulk_item.active == coupon.active

    if coupon.kind == CouponKind.fixed:
        assert bulk_item.value == coupon.value
    else:
        assert cents_to_dollars(bulk_item.value) == coupon.value

    assert bulk_item.kind == coupon.kind
    assert bulk_item.valid_till == coupon.valid_till
    assert bulk_item.quantity == coupon.quantity
    assert bulk_item.limit == coupon.limit
    assert bulk_item.minimum_order_amount == coupon.minimum_order_amount
    assert bulk_item.max_discount == coupon.max_discount
    assert bulk_item.orders_from == coupon.orders_from
    assert bulk_item.orders_to == coupon.orders_to


@pytest.mark.parametrize("kind", (CouponKind.fixed, CouponKind.percent))
async def test_should_add_or_update_coupons(
    client: AsyncClient,
    mocker: MockerFixture,
    db_connection: AsyncConnection,
    kind: CouponKind,
) -> None:
    mock_clients(mocker)
    existing_coupon_name = "eXiStInG_cOuPoN"
    existing_coupon = await CouponFactory.create(
        active=True,
        name=existing_coupon_name,
        description=None,
        value=10,
        kind=1,
        valid_till=datetime.now(),
        quantity=None,
        limit=None,
        minimum_order_amount=Decimal("10.0"),
        max_discount=Decimal("5.0"),
        user_id=None,
        token=None,
        coupon_type=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        orders_from=2,
        orders_to=4,
    )

    bulk_insert = BulkCouponModel(
        bulk_item_id=uuid4(),
        name="abCD123",
        active=True,
        value=1000,
        kind=kind,
        valid_till=datetime.now(tz=timezone.utc) + timedelta(days=1),
        quantity=1000,
        limit=2,
        minimum_order_amount=3,
        orders_from=4,
        orders_to=5,
        max_discount=6,
        users=[uuid4(), uuid4(), uuid4()],
        warehouses=[uuid4(), uuid4(), uuid4()],
        categories=[uuid4(), uuid4(), uuid4()],
    )

    bulk_update = BulkCouponModel(
        bulk_item_id=uuid4(),
        name=f"  {existing_coupon_name.lower()}  ",
        active=True,
        value=1000,
        kind=CouponKind.fixed,
        valid_till=datetime.now(tz=timezone.utc) + timedelta(days=1),
        quantity=1000,
        limit=2,
        minimum_order_amount=3,
        orders_from=4,
        orders_to=5,
        max_discount=6,
        users=[uuid4(), uuid4(), uuid4()],
        warehouses=[uuid4(), uuid4(), uuid4()],
        categories=[uuid4(), uuid4(), uuid4()],
    )
    payload = BulkCouponRequest(items=[bulk_insert, bulk_update])

    response = await client.post("/bulk/coupons", content=payload.json())
    response.raise_for_status()

    api_response = ApiResponse[BulkResponse].parse_obj(response.json())
    assert api_response and not api_response.error
    assert (result := api_response.result) and len(result.items) == 2

    item1, item2 = result.items

    assert not item1.errors and not item1.warnings
    assert not item2.errors and not item2.warnings

    assert item1.operation == BulkOperation.create
    assert item2.operation == BulkOperation.update

    assert (created_coupon := await get_coupon(db_connection, name=bulk_insert.name))
    assert (changed_coupon := await get_coupon(db_connection, name=existing_coupon.name))

    assert_is_equal(bulk_insert, created_coupon)
    assert_is_equal(bulk_update, changed_coupon)


async def test_should_return_warnings_when_no_related_data_found(
    client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    wrong_user = uuid4()
    wrong_category = uuid4()
    wrong_warehouse = uuid4()

    mock_clients(
        mocker,
        wrong_users=[wrong_user],
        wrong_categories=[wrong_category],
        wrong_warehouses=[wrong_warehouse],
    )

    bulk_insert = BulkCouponModel(
        bulk_item_id=uuid4(),
        name="NEW_COUPON",
        active=True,
        value=1000,
        kind=CouponKind.percent,
        valid_till=datetime.now(tz=timezone.utc) + timedelta(days=1),
        quantity=1000,
        limit=2,
        minimum_order_amount=3,
        orders_from=4,
        orders_to=5,
        max_discount=6,
        users=[wrong_user],
        warehouses=[wrong_warehouse],
        categories=[wrong_category],
    )

    payload = BulkCouponRequest(items=[bulk_insert])

    response = await client.post("/bulk/coupons", content=payload.json())
    response.raise_for_status()

    api_response = ApiResponse[BulkResponse].parse_obj(response.json())
    assert api_response and not api_response.error
    assert (result := api_response.result)

    item = result.items[0]
    assert not item.errors
    assert len(item.warnings) == 3

    for warning in item.warnings:
        if isinstance(warning, WarehousesNotFoundError):
            assert len(warning.data) == 1
            assert wrong_warehouse in warning.data
            continue

        if isinstance(warning, CategoriesNotFoundError):
            assert len(warning.data) == 1
            assert wrong_category in warning.data
            continue

        if isinstance(warning, UsersNotFoundError):
            assert len(warning.data) == 1
            assert wrong_user in warning.data


async def test_should_set_coupon_values(client: AsyncClient) -> None:
    coupon = await CouponFactory.create()
    value1 = BulkCouponValueModel(
        bulk_item_id=uuid4(),
        coupon_name=coupon.name,
        value=1000,
        orders_number=5,
    )

    value2 = BulkCouponValueModel(
        bulk_item_id=uuid4(),
        coupon_name=coupon.name,
        value=2000,
        orders_number=10,
    )

    payload = BulkCouponValueRequest(items=[value1, value2])
    response = await client.post("/bulk/coupons/values", content=payload.json())
    response.raise_for_status()

    api_response = ApiResponse[BulkResponse].parse_obj(response.json())

    assert api_response.error is None
    assert api_response.result and (items := api_response.result.items)
    assert len(items) == 2

    for item in items:
        assert not item.errors
        assert not item.warnings


async def test_should_skip_coupon_value_duplicates(client: AsyncClient) -> None:
    coupon = await CouponFactory.create()
    value1 = BulkCouponValueModel(
        bulk_item_id=uuid4(),
        coupon_name=coupon.name,
        value=1000,
        orders_number=5,
    )

    value2 = BulkCouponValueModel(
        bulk_item_id=uuid4(),
        coupon_name=coupon.name,
        value=2000,
        orders_number=5,
    )

    payload = BulkCouponValueRequest(items=[value1, value2])
    response = await client.post("/bulk/coupons/values", content=payload.json())
    response.raise_for_status()

    api_response = ApiResponse[BulkResponse].parse_obj(response.json())

    assert api_response.error is None
    assert api_response.result and (items := api_response.result.items)
    assert len(items) == 2

    item1, item2 = items

    assert item1.errors
    assert isinstance(error := item1.errors[0], DuplicatedItemError)
    assert error.data == item2.bulk_item_id

    assert not item2.errors
    assert not item1.warnings
    assert not item2.warnings


async def test_should_detect_duplicates(
    client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    coupon_name = "ABCDEF"
    mock_clients(mocker)

    # coupons
    coupon1 = BulkCouponModel(
        bulk_item_id=uuid4(),
        name=coupon_name,
        active=True,
        value=1000,
        kind=CouponKind.percent,
        valid_till=datetime.now(tz=timezone.utc) + timedelta(days=1),
        quantity=1000,
        limit=2,
        minimum_order_amount=3,
        orders_from=4,
        orders_to=5,
        max_discount=6,
        users=[uuid4()],
        warehouses=[uuid4()],
        categories=[uuid4()],
    )

    coupon2 = BulkCouponModel(
        bulk_item_id=uuid4(),
        name=coupon_name,
        active=True,
        value=2000,
        kind=CouponKind.fixed,
        valid_till=datetime.now(tz=timezone.utc) + timedelta(days=1),
        quantity=2000,
        limit=4,
        minimum_order_amount=6,
        orders_from=8,
        orders_to=10,
        max_discount=12,
        users=[uuid4()],
        warehouses=[uuid4()],
        categories=[uuid4()],
    )

    payload = BulkCouponRequest(items=[coupon1, coupon2])
    response = await client.post("/bulk/coupons", content=payload.json())
    response.raise_for_status()

    api_response = ApiResponse[BulkResponse].parse_obj(response.json())
    assert api_response and not api_response.error
    assert (result := api_response.result)

    item1, item2 = result.items
    assert item1.errors and len(item1.errors) == 1
    assert isinstance(item1.errors[0], DuplicatedItemError)
    assert item1.errors[0].data == coupon2.bulk_item_id
    assert not item2.errors

    # values
    coupon_value1 = BulkCouponValueModel(
        bulk_item_id=uuid4(),
        coupon_name=coupon_name,
        value=1000,
        orders_number=5,
    )

    coupon_value2 = BulkCouponValueModel(
        bulk_item_id=uuid4(),
        coupon_name=coupon_name,
        value=2000,
        orders_number=5,
    )

    payload = BulkCouponValueRequest(items=[coupon_value1, coupon_value2])
    response = await client.post("/bulk/coupons/values", content=payload.json())
    response.raise_for_status()

    api_response = ApiResponse[BulkResponse].parse_obj(response.json())
    assert api_response and not api_response.error
    assert (result := api_response.result)

    item1, item2 = result.items
    assert item1.errors and len(item1.errors) == 1
    assert isinstance(item1.errors[0], DuplicatedItemError)
    assert item1.errors[0].data == coupon_value2.bulk_item_id
    assert not item2.errors
