from datetime import date, datetime, timedelta
from uuid import uuid4

import factory

from svc.persist.schemas.bonus import WarehouseBonusSettingsSchema
from svc.persist.schemas.happy_hours import WarehouseHappyHoursScheduleSchema, WarehouseHappyHoursSettingsSchema
from tests.factories.base_factory import AsyncFactory


class WarehouseBonusSettingsFactory(AsyncFactory):
    class Meta:
        model = WarehouseBonusSettingsSchema

    warehouse_id = factory.LazyFunction(uuid4)
    required_subtotal = 1000
    bonus_fixed = None
    bonus_percent = 10
    active = True


class WarehouseHappyHoursScheduleFactory(AsyncFactory):
    class Meta:
        model = WarehouseHappyHoursScheduleSchema

    warehouse_id = factory.LazyFunction(uuid4)
    weekday = factory.LazyFunction(lambda: date.today().weekday())
    start_time = factory.LazyFunction(lambda: (datetime.now() - timedelta(hours=1)).time())
    end_time = factory.LazyFunction(lambda: (datetime.now() + timedelta(hours=1)).time())
    active = True


class WarehouseHappyHoursSettingsFactory(AsyncFactory):
    class Meta:
        model = WarehouseHappyHoursSettingsSchema

    warehouse_id = factory.LazyFunction(uuid4)
    bonus_amount = 20
