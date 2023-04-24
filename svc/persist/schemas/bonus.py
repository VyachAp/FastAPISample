from sqlalchemy import Boolean, Column, Integer
from sqlalchemy.dialects.postgresql import UUID

from svc.persist.schemas.metadata import PublicSchema


class WarehouseBonusSettingsSchema(metaclass=PublicSchema):
    __table__ = "warehouse_bonus_settings"

    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), primary_key=True)
    required_subtotal = Column("required_subtotal", Integer(), nullable=False)
    bonus_fixed = Column("bonus_fixed", Integer(), nullable=True)
    bonus_percent = Column("bonus_percent", Integer(), nullable=True)
    active = Column("active", Boolean(), nullable=False)
    happy_hours_only = Column("happy_hours_only", Boolean(), nullable=False)
