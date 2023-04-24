from datetime import datetime

import factory

from svc.persist.schemas.coupon import CouponPermitWarehouseSchema
from tests.factories.base_factory import AsyncFactory


class CouponPermitWarehouseFactory(AsyncFactory):
    class Meta:
        model = CouponPermitWarehouseSchema

    id = factory.Sequence(int)
    warehouse_id = None
    coupon_id = None
    created_at = factory.LazyFunction(datetime.utcnow)
