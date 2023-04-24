from uuid import uuid4

import pytest
from httpx import AsyncClient

from svc.api.models.conditions import ConditionsOrderItem, GetOrderConditionsRequest
from svc.api.models.order import ProductType
from tests.factories.conditions_settings import WarehouseBonusSettingsFactory


class TestBonus:
    @pytest.mark.asyncio
    async def test_bonus_should_return_discount_when_all_items_restricted_and_purchase_price_exists(
        self, client: AsyncClient, get_warehouse_mocked, mock_pricing_get_prices_with_items_purchase
    ) -> None:
        warehouse_id = uuid4()
        await WarehouseBonusSettingsFactory.create(
            bonus_fixed=None,
            bonus_percent=50,
            warehouse_id=warehouse_id,
            required_subtotal=10,
        )

        request = GetOrderConditionsRequest(
            user_id=uuid4(),
            warehouse_id=warehouse_id,
            user_order_count=5,
            coupon_applied=False,
            order_items=[
                ConditionsOrderItem(
                    id=uuid4(), product_id=uuid4(), product_type=ProductType.tobacco, actual_price=100, quantity=4
                ),
                ConditionsOrderItem(
                    id=uuid4(), product_id=uuid4(), product_type=ProductType.alcohol, actual_price=60, quantity=4
                ),
            ],
        )

        response = await client.post("/orders/conditions/calculate", content=request.json())

        assert response.status_code == 200, response.text
        assert response.json()["result"]["bonus"]["value"] == 40
