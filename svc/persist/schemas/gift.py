from sqlalchemy import BigInteger, Boolean, Column, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from svc.persist.schemas.metadata import PublicSchema, TZDateTime


class GiftPromotionSettingsSchema(metaclass=PublicSchema):
    __table__ = "gift_promotion_settings"

    id = Column("id", BigInteger, primary_key=True)
    active = Column("active", Boolean, nullable=False)
    warehouse_id = Column("warehouse_id", UUID(as_uuid=True), nullable=True)
    name = Column("name", Text, nullable=True)
    date_from = Column("date_from", TZDateTime, nullable=False)
    date_till = Column("date_till", TZDateTime, nullable=False)
    min_sum = Column("min_sum", Numeric(precision=2), nullable=False)
    less_sum_banner_id = Column("less_sum_banner_id", Integer, nullable=True)
    greater_sum_banner_id = Column("greater_sum_banner_id", Integer, nullable=True)
    created_at = Column("created_at", TZDateTime, nullable=False)
    updated_at = Column("updated_at", TZDateTime, nullable=False)


class GiftProductSchema(metaclass=PublicSchema):
    __table__ = "gift_products"

    id = Column("id", BigInteger, primary_key=True)
    gift_promotion_settings_id = Column("gift_promotion_settings_id", Integer, nullable=False)
    products_chain = Column("products_chain", JSONB, nullable=False)
    created_at = Column("created_at", TZDateTime, nullable=False)
    updated_at = Column("updated_at", TZDateTime, nullable=False)


class CartBannerSchema(metaclass=PublicSchema):
    __table__ = "cart_banners"

    id = Column("id", BigInteger, primary_key=True)
    image_url = Column("image_url", Text, nullable=True)
    style = Column("style", Integer, nullable=False)
    title = Column("title", Text, nullable=False)
    description = Column("description", Text, nullable=True)
    btn_text = Column("btn_text", Text, nullable=True)
    created_at = Column("created_at", TZDateTime, nullable=False)
    updated_at = Column("updated_at", TZDateTime, nullable=False)


class CartBannerStyleSchema(metaclass=PublicSchema):
    __table__ = "cart_banners_styles"

    id = Column("id", BigInteger, primary_key=True)
    name = Column("name", Text, nullable=False)
