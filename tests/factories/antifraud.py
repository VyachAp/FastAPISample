import factory

from svc.persist.schemas.antifraud import PromotionUserUniqueDeviceIdentifierSchema
from tests.factories.base_factory import AsyncFactory


class PromotionUserUniqueDeviceIdentifierFactory(AsyncFactory):
    class Meta:
        model = PromotionUserUniqueDeviceIdentifierSchema

    id = factory.Sequence(int)
    user_id = None
    unique_device_identifier = None
