from enum import Enum
from typing import List, Optional
from uuid import UUID

from .base_model import ApiModel
from .coupon import DistributedDiscountItemShort
from .order import OrderItem


class DeliveryMode(str, Enum):
    surge = "surge"
    normal = "normal"


class FeeType(str, Enum):
    delivery = "delivery"
    small_order = "small_order"
    packaging = "packaging"
    custom = "custom"


class ProgressBarItemType(str, Enum):
    fee = "fee"
    bonus = "bonus"
    gift = "gift"


class FeeModel(ApiModel):
    id: UUID
    name: str
    description: str
    value: int
    fee_type: FeeType
    image: Optional[str]


class Bonus(ApiModel):
    value: int


class DeliveryPromise(ApiModel):
    delivery_mode: DeliveryMode
    text: Optional[str]


class ProgressBarItem(ApiModel):
    title: str
    total_value: int
    subtitle: Optional[str]
    type: ProgressBarItemType


class PlaceholderItem(ApiModel):
    title: str


class ProgressBar(ApiModel):
    current_value: int
    image: Optional[str]
    placeholders: Optional[List[PlaceholderItem]]
    items: List[ProgressBarItem]


class OrderConditionsItem(ApiModel):
    title: str
    subtitle: Optional[str]
    image: Optional[str]
    color: Optional[str]


class OrderConditions(ApiModel):
    image: Optional[str]
    items: List[OrderConditionsItem]


class OrderConditionsResponse(ApiModel):
    fees: List[FeeModel]
    bonus: Bonus
    delivery_promise: DeliveryPromise
    catalog_progress_bar: Optional[ProgressBar]
    cart_progress_bar: Optional[ProgressBar]
    order_conditions: Optional[OrderConditions]
    distributed_discount_items: List[DistributedDiscountItemShort]


class ConditionsOrderItem(OrderItem):
    ...


class GetOrderConditionsRequest(ApiModel):
    user_id: UUID
    warehouse_id: UUID
    user_order_count: int
    coupon_applied: bool
    delivery_mode: DeliveryMode = DeliveryMode.normal
    order_items: List[ConditionsOrderItem]
    legacy_mode: bool = True
