import logging
from typing import Dict, List
from uuid import UUID

from fastapi import Depends

from svc.infrastructure.pricing.models import ProductsPricesItemCacheKey
from svc.infrastructure.pricing.pricing_adapter import PricingAdapter
from svc.services.cache import DistributedCacheRegistry

logger = logging.getLogger(__name__)


class PricingManager:
    def __init__(
        self,
        pricing_adapter: PricingAdapter = Depends(PricingAdapter),
        cache_registry: DistributedCacheRegistry = Depends(DistributedCacheRegistry),
    ) -> None:
        self._pricing_adapter = pricing_adapter
        self._cache = cache_registry

    async def get_product_prices_mapper(self, warehouse_id: UUID, product_ids: List[UUID]) -> Dict[UUID, int]:
        if not product_ids:
            return {}
        products_prices_mapper = {}
        cache_miss = []
        keys = [
            ProductsPricesItemCacheKey(
                product_id=product_id,
                warehouse_id=warehouse_id,
            )
            for product_id in product_ids
        ]
        purchase_prices = await self._cache.purchase_prices.multi_get(keys)
        for key, price in zip(keys, purchase_prices):
            if price is not None:
                products_prices_mapper[key.product_id] = price
            else:
                cache_miss.append(key.product_id)

        if cache_miss:
            product_purchase_prices = await self._pricing_adapter.get_product_prices(warehouse_id, cache_miss)
            multi_set_pairs = []
            for it in product_purchase_prices:
                multi_set_pairs.append(
                    (
                        ProductsPricesItemCacheKey(
                            product_id=it.product_id,
                            warehouse_id=warehouse_id,
                        ),
                        it.purchase_price,
                    )
                )
                products_prices_mapper[it.product_id] = it.purchase_price

            await self._cache.purchase_prices.multi_set(multi_set_pairs)

        logger.info(f"[get_product_prices_mapper] purchase_prices: {products_prices_mapper}")
        return products_prices_mapper
