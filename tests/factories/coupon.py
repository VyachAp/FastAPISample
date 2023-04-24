from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import factory

from svc.persist.schemas.coupon import CouponSchema
from tests.factories.base_factory import AsyncFactory


class CouponFactory(AsyncFactory):
    class Meta:
        model = CouponSchema

    id = factory.LazyFunction(uuid4)
    active = True
    name = factory.sequence(lambda cnt: f"coupon {cnt}")
    description = None
    value = 10
    kind = 0
    valid_till = None
    quantity = None
    limit = None
    minimum_order_amount = Decimal("10.0")
    max_discount = None
    user_id = None
    token = None
    coupon_type = 0
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    orders_from = None
    orders_to = None
