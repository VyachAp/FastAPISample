from datetime import datetime

import factory

from svc.persist.schemas.gift import GiftProductSchema
from tests.factories.base_factory import AsyncFactory


class GiftProductFactory(AsyncFactory):
    class Meta:
        model = GiftProductSchema

    id = factory.Sequence(int)
    gift_promotion_settings_id = None  # Need to fill
    products_chain = None  # Need to fill
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
