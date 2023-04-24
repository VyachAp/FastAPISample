from datetime import datetime, timedelta

import factory

from svc.persist.schemas.gift import GiftPromotionSettingsSchema
from tests.factories.base_factory import AsyncFactory


class GiftPromotionSettingsFactory(AsyncFactory):
    class Meta:
        model = GiftPromotionSettingsSchema

    id = factory.Sequence(int)
    active = True
    warehouse_id = None
    name = "default_name"
    date_from = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(days=1))
    date_till = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=3))
    min_sum = 2.0
    less_sum_banner_id = None
    greater_sum_banner_id = None
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
