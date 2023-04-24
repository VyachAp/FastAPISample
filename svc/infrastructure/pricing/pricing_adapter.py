from dataclasses import dataclass
from typing import List
from uuid import UUID

from fastapi import Depends
from pricing.api_client.client import PricingClient
from pricing.models.v2.prices import ProductPriceV2ListRequest


@dataclass
class ProductsPricesItem:
    purchase_price: int
    product_id: UUID


class PricingAdapter:
    def __init__(
        self,
        pricing_client: PricingClient = Depends(PricingClient.instance),
    ) -> None:
        self._pricing_client = pricing_client

    async def get_product_prices(self, warehouse_id: UUID, product_ids: List[UUID]) -> List[ProductsPricesItem]:
        response = await self._pricing_client.get_product_prices_cents(
            ProductPriceV2ListRequest(
                warehouse_id=warehouse_id,
                product_ids=product_ids,
            )
        )

        if response.error:
            raise Exception(response.error.code)

        if not response.result:
            return []

        return [
            ProductsPricesItem(
                purchase_price=it.purchase_price,
                product_id=it.product_id,
            )
            for it in response.result.items
        ]
