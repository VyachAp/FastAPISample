from datetime import datetime

import factory

from svc.persist.schemas.coupon import CouponPermitUserSchema
from tests.factories.base_factory import AsyncFactory


class CouponPermitUserFactory(AsyncFactory):
    class Meta:
        model = CouponPermitUserSchema

    id = factory.Sequence(int)
    user_id = None
    coupon_id = None
    created_at = factory.LazyFunction(datetime.utcnow)
