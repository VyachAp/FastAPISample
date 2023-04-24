from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from uuid import UUID

from svc.api.models.coupon import CouponKind


class CouponType(str, Enum):
    general = "general"
    referral = "referral"

    @classmethod
    def from_db_type(cls, db_value: Literal[0, 1]) -> "CouponType":
        if db_value == 0:
            return CouponType.general
        elif db_value == 1:
            return CouponType.referral
        else:
            raise ValueError(f"Wrong db_value for CouponType: {db_value}")


@dataclass
class CouponModel:
    id: UUID
    active: bool
    name: str
    description: Optional[str]
    value: int
    kind: CouponKind
    valid_till: Optional[datetime]
    quantity: Optional[int]
    limit: Optional[int]
    minimum_order_amount: Optional[int]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[UUID]
    coupon_type: CouponType
    orders_from: Optional[int]
    orders_to: Optional[int]
    max_discount: Optional[int]


@dataclass
class UserCouponModel:
    id: UUID
    coupon_id: UUID
    user_id: UUID
    order_id: UUID
    order_paid: bool
    created_at: datetime
    updated_at: datetime
