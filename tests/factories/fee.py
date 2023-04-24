from uuid import uuid4

import factory

from svc.persist.schemas.fee import FeeSchema, FeeType, UserFeeSchema, WarehouseFeeSchema
from tests.factories.base_factory import AsyncFactory


class FeeFactory(AsyncFactory):
    class Meta:
        model = FeeSchema

    id = factory.LazyFunction(uuid4)
    name = factory.sequence(lambda cnt: f"fee_name_{cnt}")
    description = "some_default_description"
    value = 125
    img_url = "http://somedefaulturl.com/img15.png"
    active = True
    fee_type = FeeType.small_order
    free_after_subtotal = 10000


class UserFeeFactory(AsyncFactory):
    class Meta:
        model = UserFeeSchema

    user_id = factory.LazyFunction(uuid4)
    fee_id = factory.LazyFunction(uuid4)


class WarehouseFeeFactory(AsyncFactory):
    class Meta:
        model = WarehouseFeeSchema

    warehouse_id = factory.LazyFunction(uuid4)
    fee_id = factory.LazyFunction(uuid4)
