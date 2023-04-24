from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.database import database
from svc.persist.schemas.antifraud import (
    PromotionDeviceIdentifierWhitelist,
    PromotionUserAntifraudWhitelistSchema,
    PromotionUserUniqueDeviceIdentifierSchema,
)
from svc.settings import Settings, get_service_settings


class AntifraudManager:
    def __init__(
        self,
        connection: AsyncConnection = Depends(database.connection),
        config: Settings = Depends(get_service_settings),
    ):
        self._connection = connection
        self._config = config

    async def get_amount_of_users_by_identifier(self, unique_identifier: str, user_id: UUID) -> int:
        select_statement = (
            select(func.count(PromotionUserUniqueDeviceIdentifierSchema.user_id).label("user_count"))
            .select_from(PromotionUserUniqueDeviceIdentifierSchema.table)
            .where(PromotionUserUniqueDeviceIdentifierSchema.unique_device_identifier == unique_identifier)
            .where(PromotionUserUniqueDeviceIdentifierSchema.user_id != user_id)
        )
        entity = (await self._connection.execute(select_statement)).first()
        return entity["user_count"] if entity is not None else 0

    async def is_user_whitelisted(self, user_id: UUID) -> bool:
        from_statement = PromotionUserAntifraudWhitelistSchema.table
        select_statement = (
            select(PromotionUserAntifraudWhitelistSchema.id)
            .select_from(from_statement)
            .where(PromotionUserAntifraudWhitelistSchema.user_id == user_id)
        )
        entity = (await self._connection.execute(select_statement)).first()
        if not entity:
            return False
        return True

    async def is_identifier_whitelisted(self, identifier: str) -> bool:
        from_statement = PromotionDeviceIdentifierWhitelist.table
        select_statement = (
            select(PromotionDeviceIdentifierWhitelist.id)
            .select_from(from_statement)
            .where(PromotionDeviceIdentifierWhitelist.device_identifier == identifier)
        )
        entity = (await self._connection.execute(select_statement)).first()
        if not entity:
            return False
        return True

    async def register_fingerprint_usage(self, user_id: UUID, identifier: str) -> None:
        stmt = (
            insert(PromotionUserUniqueDeviceIdentifierSchema.table)
            .values(
                {
                    PromotionUserUniqueDeviceIdentifierSchema.user_id: user_id,
                    PromotionUserUniqueDeviceIdentifierSchema.unique_device_identifier: identifier,
                }
            )
            .on_conflict_do_nothing(
                index_elements=[
                    PromotionUserUniqueDeviceIdentifierSchema.user_id,
                    PromotionUserUniqueDeviceIdentifierSchema.unique_device_identifier,
                ]
            )
        )

        await self._connection.execute(stmt)
