from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from tests.factories.cart_banner import CartBannerFactory, CartBannerStyleFactory
from tests.factories.gift_product import GiftProductFactory
from tests.factories.gift_promotion_setting import GiftPromotionSettingsFactory


class TestGetGiftAndBanner:
    @pytest.mark.asyncio
    async def test_get_gift(self, client: AsyncClient) -> None:
        warehouse_id = uuid4()
        for id_, name in ((1, "info"), (2, "done")):
            await CartBannerStyleFactory.create(id=id_, name=name)

        banner = await CartBannerFactory.create()
        settings = await GiftPromotionSettingsFactory.create(
            warehouse_id=warehouse_id,
            greater_sum_banner_id=banner.id,
            less_sum_banner_id=banner.id,
        )
        prod_ids = (uuid4(), uuid4())
        await GiftProductFactory.create(
            gift_promotion_settings_id=settings.id,
            products_chain=[{"product_id": str(it), "quantity": 2} for it in prod_ids],
        )

        # Call service
        request_data = {
            "warehouse_id": str(warehouse_id),
            "order_subtotal": 5000,
        }
        response = await client.post("/gifts", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["gift_settings_id"] == settings.id
        chain = body["gifts_chain"]
        assert len(chain) == 2
        for it in chain:
            assert it["quantity"] == 2
            assert UUID(it["product_id"]) in prod_ids

        request_data["order_subtotal"] = 100
        response = await client.post("/gifts", json=request_data)
        assert response.json()["error"]

    @pytest.mark.asyncio
    async def test_get_banner(self, client: AsyncClient) -> None:
        warehouse_id = uuid4()
        for id_, name in ((1, "info"), (2, "done")):
            await CartBannerStyleFactory.create(id=id_, name=name)

        banner = await CartBannerFactory.create()
        settings = await GiftPromotionSettingsFactory.create(
            warehouse_id=warehouse_id,
            greater_sum_banner_id=banner.id,
            less_sum_banner_id=banner.id,
        )
        prod_ids = (uuid4(), uuid4())
        await GiftProductFactory.create(
            gift_promotion_settings_id=settings.id,
            products_chain=[{"product_id": str(it), "quantity": 2} for it in prod_ids],
        )

        # Call service
        request_data = {
            "warehouse_id": str(warehouse_id),
            "order_subtotal": 5000,
        }
        response = await client.post("/banner", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["result"]
        banner = body["banner"]
        assert banner
        assert banner["btn_text"] == CartBannerFactory.btn_text
        assert banner["description"] == CartBannerFactory.description
        assert banner["img_url"] == CartBannerFactory.image_url
        assert banner["style"] == "done"
        assert banner["title"] == CartBannerFactory.title

        request_data["order_subtotal"] = 100
        response = await client.post("/banner", json=request_data)
        assert response.status_code == 200
        body = response.json()["result"]
        banner = body["banner"]
        assert banner
        assert banner["style"] == "info"

    @pytest.mark.asyncio
    async def test_gift_settings_min_sum_error(self, client: AsyncClient) -> None:
        warehouse_id = uuid4()
        for id_, name in ((1, "info"), (2, "done")):
            await CartBannerStyleFactory.create(id=id_, name=name)

        banner = await CartBannerFactory.create(id=3)
        settings = await GiftPromotionSettingsFactory.create(
            warehouse_id=warehouse_id,
            greater_sum_banner_id=banner.id,
            less_sum_banner_id=banner.id,
        )
        prod_ids = (uuid4(), uuid4())
        await GiftProductFactory.create(
            gift_promotion_settings_id=settings.id,
            products_chain=[{"product_id": str(it), "quantity": 2} for it in prod_ids],
        )

        # Call service
        request_data = {
            "warehouse_id": str(warehouse_id),
            "order_subtotal": 100,
        }
        response = await client.post("/gifts", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "gift_settings_min_sum"

    @pytest.mark.asyncio
    async def test_gift_settings_not_found(self, client: AsyncClient) -> None:
        warehouse_id = uuid4()

        # Call service
        request_data = {
            "warehouse_id": str(warehouse_id),
            "order_subtotal": 100,
        }
        response = await client.post("/gifts", json=request_data)

        # Check Response
        assert response.status_code == 200
        body = response.json()["error"]
        assert body["code"] == "gift_settings_not_found"
