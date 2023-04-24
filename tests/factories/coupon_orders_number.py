from datetime import datetime

import factory

from svc.persist.schemas.coupon import CouponValueOrderNumberSchema
from tests.factories.base_factory import AsyncFactory


class CouponOrderNumber(AsyncFactory):
    class Meta:
        model = CouponValueOrderNumberSchema

    id = factory.Sequence(int)
    coupon_id = None
    coupon_value = 10
    orders_number = None
    created_at = factory.LazyFunction(datetime.utcnow)
