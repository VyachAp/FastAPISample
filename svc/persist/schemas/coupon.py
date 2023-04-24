from enum import Enum

from citext import CIText
from sqlalchemy import BigInteger, Boolean, Column, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from svc.persist.schemas.metadata import PublicSchema, TZDateTime


class CouponKindDb(Enum):
    percent = 0
    fixed = 1


class CouponTypeDb(int, Enum):
    general = 0
    referral = 1


class CouponSchema(metaclass=PublicSchema):
    __table__ = "coupons"

    id = Column("id", UUID(as_uuid=True), primary_key=True)
    active = Column("active", Boolean, nullable=False, default=True)
    name = Column("name", CIText, nullable=False)
    description = Column("description", String, nullable=True)
    value = Column("value", Numeric(precision=2), nullable=False)
    kind = Column("kind", Integer, nullable=False)
    valid_till = Column("valid_till", TZDateTime, nullable=True)
    quantity = Column("quantity", Integer, nullable=True)
    limit = Column("limit", Integer, nullable=True)
    minimum_order_amount = Column("minimum_order_amount", Numeric(precision=2), nullable=True)
    created_at = Column("created_at", TZDateTime, nullable=False)
    updated_at = Column("updated_at", TZDateTime, nullable=False)
    user_id = Column("user_id", UUID(as_uuid=True), nullable=True)
    token = Column("token", String, nullable=True)
    coupon_type = Column("coupon_type", Integer, nullable=False, default=0)
    orders_from = Column("orders_from", Integer, nullable=True)
    orders_to = Column("orders_to", Integer, nullable=True)
    referral_active = Column("referral_active", Boolean, nullable=True)
    max_discount = Column("max_discount", Numeric(precision=2), nullable=True)


class UserCouponSchema(metaclass=PublicSchema):
    __table__ = "users_coupons"

    id = Column("id", UUID(as_uuid=True), primary_key=True)
    user_id = Column("user_id", UUID(as_uuid=True), nullable=False)
    coupon_id = Column("coupon_id", UUID(as_uuid=True), nullable=False)
    order_id = Column("order_id", UUID(as_uuid=True), nullable=False)
    order_paid = Column("order_paid", Boolean, nullable=False)
    created_at = Column("created_at", TZDateTime, nullable=False)
    updated_at = Column("updated_at", TZDateTime, nullable=False)


class CouponPermitCategorySchema(metaclass=PublicSchema):
    __table__ = "coupons_permit_categories"

    id = Column("id", BigInteger, primary_key=True)
    category_id = Column("category_id", UUID(as_uuid=True), nullable=False)
    coupon_id = Column("coupon_id", UUID(as_uuid=True), nullable=False)
    created_at = Column("created_at", TZDateTime, nullable=False)


class CouponPermitUserSchema(metaclass=PublicSchema):
    __table__ = "coupons_permit_users"

    id = Column("id", BigInteger, primary_key=True)
    user_id = Column("user_id", UUID(as_uuid=True), nullable=False)
    coupon_id = Column("coupon_id", UUID(as_uuid=True), nullable=False)
    created_at = Column("created_at", TZDateTime, nullable=False)


class CouponPermitWarehouseSchema(metaclass=PublicSchema):
    __table__ = "coupons_permit_warehouses"

    id = Column("id", BigInteger, primary_key=True)
    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), nullable=False)
    coupon_id = Column("coupon_id", UUID(as_uuid=True), nullable=False)
    created_at = Column("created_at", TZDateTime, nullable=False)


class CouponValueOrderNumberSchema(metaclass=PublicSchema):
    __table__ = "coupons_value_orders_number"

    id = Column("id", BigInteger, primary_key=True)
    coupon_id = Column("coupon_id", UUID(as_uuid=True), nullable=False)
    coupon_value = Column("coupon_value", Numeric(precision=2), nullable=False)
    orders_number = Column("orders_number", Integer, nullable=False)
    created_at = Column("created_at", TZDateTime, nullable=False)
