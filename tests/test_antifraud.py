from datetime import datetime, timedelta
from typing import Callable, Optional
from uuid import uuid4

import pytest
from httpx import AsyncClient

from svc.api.models.error_code import ErrorCode
from tests.factories.antifraud import PromotionUserUniqueDeviceIdentifierFactory
from tests.factories.coupon import CouponFactory


class TestAntifraud:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "valid_till_getter",
        [
            lambda: None,
            lambda: (datetime.utcnow() + timedelta(minutes=20)),
        ],
    )
    async def test_antifraud(
        self,
        client: AsyncClient,
        valid_till_getter: Callable[[], Optional[datetime]],
    ) -> None:
        user_id = uuid4()
        order_id = uuid4()
        warehouse_id = uuid4()
        unique_identifier = "abcdefg"
        coupon = await CouponFactory.create(quantity=5, name="some", valid_till=valid_till_getter())
        for i in range(4):
            await PromotionUserUniqueDeviceIdentifierFactory.create(
                user_id=uuid4(), unique_device_identifier=unique_identifier
            )

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
                    "categories_ids": [str(uuid4())],
                    "product_id": str(uuid4()),
                    "subtotal": 5000,
                    "product_type": "regular",
                    "actual_price": 2500,
                    "quantity": 2,
                    "id": str(uuid4()),
                }
            ],
            "unique_identifier": unique_identifier,
        }
        response = await client.post(f"/coupons/orders/{order_id}", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["error"]["code"] == ErrorCode.user_not_eligible_to_use_coupon
