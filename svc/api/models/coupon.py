from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import NonNegativeInt, StrictInt

from .base_model import ApiModel
from .order import OrderItem


class CouponKind(str, Enum):
    percent = "percent"
    fixed = "fixed"

    @classmethod
    def from_db_type(cls, db_value: int) -> "CouponKind":
        if db_value == 0:
            return CouponKind.percent
        elif db_value == 1:
            return CouponKind.fixed
        else:
            raise ValueError(f"Wrong db_value for CouponKind: {db_value}")

    def to_db_type(self) -> int:
        if self is CouponKind.percent:
            return 0
        elif self is CouponKind.fixed:
            return 1
        else:
            raise ValueError(f"Wrong value of CouponKind: {self}")


class DistributedDiscountItemShort(ApiModel):
    order_item_id: UUID
    distributed_discount: int


class CouponDetail(ApiModel):
    id: UUID
    name: str
    kind: CouponKind
    value: StrictInt
    min_order_amount: Optional[StrictInt]


class CouponOrderItem(OrderItem):
    categories_ids: List[UUID]
    subtotal: NonNegativeInt


class OrderCouponDetail(CouponDetail):
    order_id: Optional[UUID]
    discount_amount: NonNegativeInt
    cart_message_args: Optional[Dict[str, Any]]
    distributed_discount_items: List[DistributedDiscountItemShort]


class AddOrderCouponRequest(ApiModel):
    user_id: UUID
    warehouse_id: UUID
    name: str
    order_subtotal: NonNegativeInt
    paid_orders_count: StrictInt
    delivered_orders_count: StrictInt
    order_items: List[CouponOrderItem]
    unique_identifier: Optional[str]


class RecalculateOrderCouponRequest(ApiModel):
    order_subtotal: NonNegativeInt
    paid_orders_count: StrictInt
    delivered_orders_count: StrictInt
    warehouse_id: UUID
    order_items: List[CouponOrderItem]


class CreateReferralCouponRequest(ApiModel):
    user_id: UUID
