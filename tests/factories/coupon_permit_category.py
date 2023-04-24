from datetime import datetime

import factory

from svc.persist.schemas.coupon import CouponPermitCategorySchema
from tests.factories.base_factory import AsyncFactory


class CouponPermitCategoryFactory(AsyncFactory):
    class Meta:
        model = CouponPermitCategorySchema

    id = factory.Sequence(int)
    category_id = None
    coupon_id = None
    created_at = factory.LazyFunction(datetime.utcnow)
