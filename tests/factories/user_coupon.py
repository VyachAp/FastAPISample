from datetime import datetime
from uuid import uuid4

import factory

from svc.persist.schemas.coupon import UserCouponSchema
from tests.factories.base_factory import AsyncFactory


class UserCouponFactory(AsyncFactory):
    class Meta:
        model = UserCouponSchema

    id = factory.LazyFunction(uuid4)
    user_id = None
    coupon_id = None
    order_id = None
    order_paid = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
