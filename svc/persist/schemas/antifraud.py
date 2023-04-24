from sqlalchemy import BigInteger, Column, String
from sqlalchemy.dialects.postgresql import UUID

from svc.persist.schemas.metadata import PublicSchema


class PromotionUserUniqueDeviceIdentifierSchema(metaclass=PublicSchema):
    __table__ = "promotion_user_unique_device_identifier"

    id = Column("id", BigInteger, primary_key=True)
    user_id = Column("user_id", UUID(as_uuid=True), nullable=False)
    unique_device_identifier = Column("unique_device_identifier", String, nullable=False)


class PromotionUserAntifraudWhitelistSchema(metaclass=PublicSchema):
    __table__ = "promotion_user_antifraud_whitelist"

    id = Column("id", BigInteger, primary_key=True)
    user_id = Column("user_id", UUID(as_uuid=True), nullable=False)


class PromotionDeviceIdentifierWhitelist(metaclass=PublicSchema):
    __table__ = "promotion_device_identifier_whitelist"

    id = Column("id", BigInteger, primary_key=True)
    device_identifier = Column("device_identifier", String, nullable=False)
