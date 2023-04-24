from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Dict, Optional
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.schemas.coupon import CouponTypeDb
from svc.services.coupon.dto import CouponType
from svc.settings import get_service_settings
from svc.utils.money import dollars_to_cents
from tests.factories.coupon import CouponFactory
from tests.factories.coupon_orders_number import CouponOrderNumber
from tests.factories.coupon_permit_category import CouponPermitCategoryFactory
from tests.factories.coupon_permit_user import CouponPermitUserFactory
from tests.factories.coupon_permit_warehouse import CouponPermitWarehouseFactory
from tests.factories.user_coupon import UserCouponFactory

from .helpers import get_coupon, get_user_coupon


class TestGetCoupon:
    @pytest.mark.asyncio
    async def test_should_return_coupon(self, client: AsyncClient) -> None:
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id

        # Call service
        response = await client.get(f"/coupons/{coupon_id}")

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)

    @pytest.mark.asyncio
    async def test_should_fail_coupon_not_found(self, client: AsyncClient) -> None:
        coupon_id = uuid4()
        await CouponFactory.create(quantity=5)

        # Call service
        response = await client.get(f"/coupons/{coupon_id}")

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_not_found"


class TestAddCoupon:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "valid_till_getter",
        [
            lambda: None,
            lambda: (datetime.utcnow() + timedelta(minutes=20)),
        ],
    )
    async def test_should_add_coupon(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
        valid_till_getter: Callable[[], Optional[datetime]],
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, name="some", valid_till=valid_till_getter())
        coupon_id = coupon.id
        unique_identifier = "abcdefg"

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name.upper(),
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
            "unique_identifier": unique_identifier,
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["cart_message_args"] is None
        assert body["discount_amount"] == 500

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity - db_coupon.quantity == 1
        assert db_user_coupon

    @pytest.mark.asyncio
    async def test_coupon_value_depends_on_orders_number(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        second_coupon = await CouponFactory.create(quantity=5, value=10)
        await CouponOrderNumber.create(coupon_id=coupon.id, coupon_value=50, orders_number=1)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name.upper(),
            "order_subtotal": 5000,
            "paid_orders_count": 0,
            "delivered_orders_count": 0,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["cart_message_args"] is None
        assert body["discount_amount"] == 2500

        request_data["name"] = second_coupon.name.upper()
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["cart_message_args"] is None
        assert body["discount_amount"] == 500

        request_data["delivered_orders_count"] = 1
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["cart_message_args"] is None
        assert body["discount_amount"] == 500

    @pytest.mark.parametrize(
        "max_discount, kind, exp_args, exp_discount",
        [
            (2, 0, {"max_discount": 200}, 200),
            (4, 0, {"max_discount": 400}, 400),
            (5, 0, None, 500),
            (2, 1, None, 1000),
            (None, 0, None, 500),
        ],
    )
    @pytest.mark.asyncio
    async def test_max_discount(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
        max_discount: Optional[int],
        kind: int,
        exp_args: Optional[Dict[str, int]],
        exp_discount: int,
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, name="some", max_discount=max_discount, kind=kind)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name.upper(),
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["cart_message_args"] == exp_args
        assert body["discount_amount"] == exp_discount

    @pytest.mark.asyncio
    async def test_permitted_coupon_user(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        order_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await CouponPermitUserFactory.create(user_id=user_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(uuid4()),
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity - db_coupon.quantity == 1
        assert db_user_coupon

    @pytest.mark.asyncio
    async def test_not_permitted_coupon_user(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        second_user_id = uuid4()
        order_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await CouponPermitUserFactory.create(user_id=second_user_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(uuid4()),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_not_permitted_user"

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity == db_coupon.quantity
        assert not db_user_coupon

    @pytest.mark.asyncio
    async def test_should_fail_coupon_not_found_by_name(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": "Some coupon name",
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_not_valid"

        # Check DB objects
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon.id,
            order_id=order_id,
        )
        assert not db_user_coupon, "UserCoupon should not be created"

    @pytest.mark.asyncio
    async def test_should_fail_coupon_expired(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, valid_till=datetime.utcnow())

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": "Some coupon name",
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_not_valid"

        # Check DB objects
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon.id,
            order_id=order_id,
        )
        assert not db_user_coupon, "UserCoupon should not be created"

    @pytest.mark.asyncio
    async def test_should_fail_coupon_redeemed_error_with_limit(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, limit=2)
        await UserCouponFactory.create(coupon_id=coupon.id, order_id=uuid4(), user_id=user_id, order_paid=True)
        await UserCouponFactory.create(coupon_id=coupon.id, order_id=uuid4(), user_id=user_id, order_paid=True)
        await UserCouponFactory.create(coupon_id=coupon.id, order_id=uuid4(), user_id=user_id, order_paid=True)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_redeemed_limit"
        assert body["error"]["data"]["limit"] == coupon.limit

    @pytest.mark.asyncio
    async def test_should_fail_coupon_redeemed_error_orders_from(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, orders_from=3)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 2,
            "delivered_orders_count": 2,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_redeemed_orders_from"
        assert body["error"]["data"]["missing_orders_amount"] == coupon.orders_from - request_data["paid_orders_count"]

    @pytest.mark.asyncio
    async def test_should_fail_coupon_redeemed_error_orders_to(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, orders_to=3)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 3,
            "delivered_orders_count": 3,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_redeemed_orders_to"
        assert body["error"]["data"]["orders_amount_upper_limit"] == coupon.orders_to

    @pytest.mark.asyncio
    async def test_should_fail_coupon_redeemed_error_quantity_is_zero(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=0)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 3,
            "delivered_orders_count": 3,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_redeemed"

    @pytest.mark.asyncio
    async def test_should_fail_coupon_min_amount(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 999,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "coupon_min_amount"
        assert Decimal(body["error"]["data"]["min_amount"]) == coupon.minimum_order_amount

    @pytest.mark.asyncio
    async def test_should_fail_referral_coupon_self_usage(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, user_id=user_id, coupon_type=CouponTypeDb.referral)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "referral_coupon_self_usage"

    @pytest.mark.asyncio
    async def test_should_fail_referral_coupon_limit(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, coupon_type=CouponTypeDb.referral, orders_to=5)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 10,
            "delivered_orders_count": 10,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == "referral_coupon_limit"
        assert body["error"]["data"]["initial_orders_count_permit"] == coupon.orders_to

    @pytest.mark.asyncio
    async def test_should_create_referral_coupon(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()

        # Call service
        request_data = {
            "user_id": str(user_id),
            "token": None,
        }
        response = await client.post("/coupons/referral", json=request_data)

        # Check Response
        assert response.status_code == 200
        coupon_name = response.json()["result"]
        assert isinstance(coupon_name, str), "Should return created Coupon.name"

        # Check objects at DB
        db_coupon = await get_coupon(db_connection, name=coupon_name)
        assert db_coupon, "Coupon should be found by name"
        assert db_coupon.coupon_type == CouponType.referral, "Coupon.coupon_type should be referral"
        conf = get_service_settings()
        assert db_coupon.max_discount == conf.referral_coupon.max_discount

        response = await client.post("/coupons/referral", json=request_data)
        assert response.json()["result"] == coupon_name

    @pytest.mark.asyncio
    async def test_permitted_coupon_warehouse(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await CouponPermitWarehouseFactory.create(warehouse_id=warehouse_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity - db_coupon.quantity == 1
        assert db_user_coupon

    @pytest.mark.asyncio
    async def test_not_permitted_coupon_warehouse(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        second_warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await CouponPermitWarehouseFactory.create(warehouse_id=second_warehouse_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "warehouse_id": str(warehouse_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_not_permitted_warehouse"

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity == db_coupon.quantity
        assert not db_user_coupon

    @pytest.mark.asyncio
    async def test_permitted_coupon_categories(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        order_id = uuid4()
        category_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await CouponPermitCategoryFactory.create(category_id=category_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "name": coupon.name,
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(uuid4()),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(category_id)],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity - db_coupon.quantity == 1
        assert db_user_coupon

    @pytest.mark.asyncio
    async def test_not_permitted_coupon_categories(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        order_id = uuid4()
        category_id = uuid4()
        permitted_category_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await CouponPermitCategoryFactory.create(category_id=permitted_category_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "user_id": str(user_id),
            "name": coupon.name,
            "warehouse_id": str(uuid4()),
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(category_id)],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_not_permitted_categories"
        assert body["data"]["permitted_categories_ids"] == [str(permitted_category_id)]

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon_id,
            order_id=order_id,
        )
        assert coupon.quantity == db_coupon.quantity
        assert not db_user_coupon


class TestDeleteCoupon:
    @pytest.mark.asyncio
    async def test_should_delete_coupon(self, client: AsyncClient, db_connection: AsyncConnection) -> None:
        user_id = uuid4()
        order_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        response = await client.delete(f"/coupons/{coupon_id}/orders/{order_id}")

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)

        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        assert db_coupon.quantity - coupon.quantity == 1, "Coupon.quantity should be reverted"
        db_user_coupon = await get_user_coupon(
            db_connection,
            coupon_id=coupon.id,
            order_id=order_id,
        )
        assert not db_user_coupon, "UserCoupon should be deleted"


class TestRecalculateCoupon:
    @pytest.mark.asyncio
    async def test_should_return_recalculated_coupon_absolute_discount(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=1, value=15)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(warehouse_id),
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == dollars_to_cents(coupon.value)

    @pytest.mark.asyncio
    async def test_coupon_value_depends_on_orders_number(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=1, value=15)
        second_coupon = await CouponFactory.create(quantity=5, kind=1, value=5)
        new_coupon_value = await CouponOrderNumber.create(coupon_id=coupon.id, coupon_value=37, orders_number=6)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(warehouse_id),
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == dollars_to_cents(new_coupon_value.coupon_value)

        response = await client.post(f"/coupons/{second_coupon.id}/orders/{order_id}", json=request_data)
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["id"] == str(second_coupon.id)
        assert body["discount_amount"] == dollars_to_cents(second_coupon.value)

        request_data["delivered_orders_count"] = 4
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)
        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == dollars_to_cents(coupon.value)

    @pytest.mark.parametrize(
        "max_discount, kind, exp_args, exp_discount",
        [
            (2, 0, {"max_discount": 200}, 200),
            (4, 0, {"max_discount": 400}, 400),
            (5, 0, None, 500),
            (2, 1, None, 1000),
            (None, 0, None, 500),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_return_recalculated_coupon_with_max_discount(
        self,
        client: AsyncClient,
        max_discount: Optional[int],
        kind: int,
        exp_args: Optional[Dict[str, int]],
        exp_discount: int,
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, max_discount=max_discount, kind=kind)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(warehouse_id),
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == exp_discount
        assert body["cart_message_args"] == exp_args

    @pytest.mark.asyncio
    async def test_should_truncate_if_discount_greater_than_order_subtotal(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=1, value=100, minimum_order_amount=4)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 500,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 500,
                    "product_type": "regular",
                    "actual_price": 100,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(warehouse_id),
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == 450

    @pytest.mark.asyncio
    async def test_should_return_recalculated_coupon_percent_discount(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, value=20)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(warehouse_id),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == request_data["order_subtotal"] * coupon.value / Decimal("100.0")

    @pytest.mark.asyncio
    async def test_should_return_cart_message_orders_from(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, orders_from=3)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 2,
            "delivered_orders_count": 2,
            "warehouse_id": str(warehouse_id),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_redeemed_orders_from"
        assert body["data"]["missing_orders_amount"] == coupon.orders_from - request_data["paid_orders_count"]
        assert body["data"]["coupon_name"] == coupon.name

    @pytest.mark.asyncio
    async def test_should_return_cart_message_orders_to(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, orders_to=3)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 3,
            "delivered_orders_count": 3,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(warehouse_id),
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_redeemed_orders_to"
        assert body["data"]["orders_amount_upper_limit"] == coupon.orders_to
        assert body["data"]["coupon_name"] == coupon.name

    @pytest.mark.asyncio
    async def test_should_return_cart_message_min_amount(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 999,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(uuid4()),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 999,
                    "product_type": "regular",
                    "actual_price": 999,
                    "quantity": 1,
                }
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_min_amount"
        assert Decimal(body["data"]["min_amount"]) == coupon.minimum_order_amount
        assert body["data"]["coupon_name"] == coupon.name

    @pytest.mark.asyncio
    async def test_permitted_categories(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        not_permitted_category_id = uuid4()
        category_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=0, value=25, minimum_order_amount=Decimal("1"))
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)
        await CouponPermitCategoryFactory.create(category_id=category_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "order_subtotal": 900,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(uuid4()),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(category_id)],
                    "product_id": str(uuid4()),
                    "subtotal": 250,
                    "product_type": "regular",
                    "actual_price": 250,
                    "quantity": 1,
                },
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(category_id)],
                    "product_id": str(uuid4()),
                    "subtotal": 150,
                    "product_type": "regular",
                    "actual_price": 150,
                    "quantity": 1,
                },
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(not_permitted_category_id)],
                    "product_id": str(uuid4()),
                    "subtotal": 500,
                    "product_type": "regular",
                    "actual_price": 500,
                    "quantity": 1,
                },
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == 100

    @pytest.mark.asyncio
    async def test_not_permitted_categories(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        category_id = uuid4()
        permitted_category_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=1, value=15)
        warehouse_id = uuid4()
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)
        await CouponPermitCategoryFactory.create(category_id=permitted_category_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(category_id)],
                    "product_id": str(uuid4()),
                    "subtotal": 50,
                    "product_type": "regular",
                    "actual_price": 10,
                    "quantity": 5,
                }
            ],
            "warehouse_id": str(warehouse_id),
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_not_permitted_categories"
        assert body["data"]["permitted_categories_ids"] == [str(permitted_category_id)]
        assert body["data"]["coupon_name"] == coupon.name

    @pytest.mark.asyncio
    async def test_permitted_warehouse(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=1, value=15)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)
        await CouponPermitWarehouseFactory.create(warehouse_id=warehouse_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(warehouse_id),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body
        assert body["id"] == str(coupon_id)
        assert body["discount_amount"] == dollars_to_cents(coupon.value)

    @pytest.mark.asyncio
    async def test_not_permitted_warehouse(self, client: AsyncClient) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        second_warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, kind=1, value=15)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)
        await CouponPermitWarehouseFactory.create(warehouse_id=second_warehouse_id, coupon_id=coupon_id)

        # Call service
        request_data = {
            "order_subtotal": 5000,
            "paid_orders_count": 5,
            "delivered_orders_count": 5,
            "warehouse_id": str(warehouse_id),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 1000,
                    "quantity": 5,
                }
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "coupon_not_permitted_warehouse"
        assert body["data"]["coupon_name"] == coupon.name

    @pytest.mark.asyncio
    async def test_should_return_recalculated_coupon_when_coupon_subtotal_less_minimum_but_alco(
        self, client: AsyncClient
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        coupon = await CouponFactory.create(quantity=5, value=80, minimum_order_amount=None)
        coupon_id = coupon.id
        await UserCouponFactory.create(coupon_id=coupon_id, user_id=user_id, order_id=order_id)

        # Call service
        request_data = {
            "order_subtotal": 200,
            "paid_orders_count": 0,
            "delivered_orders_count": 0,
            "warehouse_id": str(warehouse_id),
            "order_items": [
                {
                    "id": str(uuid4()),
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 200,
                    "product_type": "alcohol",
                    "actual_price": 200,
                    "quantity": 1,
                }
            ],
        }
        response = await client.post(f"/coupons/{coupon_id}/orders/{order_id}", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()
        result = body["result"]
        assert result, f"{body}"
        assert result["id"] == str(coupon_id)
        assert result["discount_amount"] == 70
