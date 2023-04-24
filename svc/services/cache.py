from uuid import UUID

from aiocache import Cache
from internal_lib.entry import CacheMapEntry
from internal_lib.registry import CacheRegistry

from svc.infrastructure.pricing.models import ProductsPricesItemCacheKey
from svc.infrastructure.warehouse.models import WarehouseShortModel
from svc.settings import get_cache_config, get_distributed_cache_config


class LocalCacheRegistry(CacheRegistry):
    _settings = get_cache_config()
    _cache = Cache(Cache.MEMORY)

    warehouses: CacheMapEntry[UUID, WarehouseShortModel] = CacheMapEntry[UUID, WarehouseShortModel](
        _cache, "warehouses", ttl=_settings.warehouses_ttl
    )


class DistributedCacheRegistry:
    _settings = get_distributed_cache_config()
    _cache = Cache.from_url(_settings.url)

    purchase_prices: CacheMapEntry[ProductsPricesItemCacheKey, int] = CacheMapEntry[ProductsPricesItemCacheKey, int](
        _cache,
        "purchase_prices",
        ttl=_settings.purchase_price_ttl,
        dumps_fn=str,
        loads_fn=int,
    )
