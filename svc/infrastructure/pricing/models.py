from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProductsPricesItemCacheKey:
    product_id: UUID
    warehouse_id: UUID
