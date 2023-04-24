from sqlalchemy import Boolean, Column, DateTime, Integer, Time
from sqlalchemy.dialects.postgresql import UUID

from svc.persist.schemas.metadata import PublicSchema


class WarehouseHappyHoursScheduleSchema(metaclass=PublicSchema):
    __table__ = "warehouse_happy_hours"

    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), primary_key=True)
    weekday = Column("weekday", Integer(), nullable=False, primary_key=True)
    start_time = Column("start_time", Time(), nullable=False, primary_key=True)
    end_time = Column("end_time", Time(), nullable=False)
    active = Column("active", Boolean(), nullable=False)


class WarehouseForcedHappyHoursSchema(metaclass=PublicSchema):
    __table__ = "warehouse_forced_happy_hours"

    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), primary_key=True)
    start_time = Column("start_time", DateTime(), nullable=False, primary_key=True)
    end_time = Column("end_time", DateTime(), nullable=True, primary_key=True)


class WarehouseHappyHoursSettingsSchema(metaclass=PublicSchema):
    __table__ = "warehouse_happy_hours_settings"

    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), primary_key=True)
    bonus_amount = Column("bonus_amount", Integer(), nullable=False)
