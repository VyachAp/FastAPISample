import enum

from sqlalchemy import Boolean, Column, Integer, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID

from svc.persist.schemas.metadata import PublicSchema


class FeeType(str, enum.Enum):
    delivery = "delivery"
    small_order = "small_order"
    packaging = "packaging"
    custom = "custom"


class FeeSchema(metaclass=PublicSchema):
    __table__ = "fees"

    id = Column("id", UUID(as_uuid=True), primary_key=True)
    name = Column("name", Text(), nullable=False, unique=True)
    description = Column("description", Text, nullable=False)
    value = Column("value", Integer(), nullable=False)
    img_url = Column("img_url", Text(), nullable=True)
    active = Column("active", Boolean(), nullable=False)
    fee_type = Column("fee_type", ENUM(FeeType, name="fee_type"), nullable=False)
    free_after_subtotal = Column("free_after_subtotal", Integer(), nullable=True)


class UserFeeSchema(metaclass=PublicSchema):
    __table__ = "user_fees"

    user_id = Column("user_id", UUID(as_uuid=True), primary_key=True)
    fee_id = Column("fee_id", UUID(as_uuid=True), primary_key=True)


class WarehouseFeeSchema(metaclass=PublicSchema):
    __table__ = "warehouse_fees"

    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), primary_key=True)
    fee_id = Column("fee_id", UUID(as_uuid=True), primary_key=True)
