from enum import Enum
from uuid import UUID

from .base_model import ApiModel


class ProductType(str, Enum):
    regular = "regular"
    tobacco = "tobacco"
    alcohol = "alcohol"


class OrderItem(ApiModel):
    id: UUID
    product_id: UUID
    product_type: ProductType
    actual_price: int
    quantity: int
