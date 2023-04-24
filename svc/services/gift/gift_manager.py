import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.database import database
from svc.persist.schemas.gift import CartBannerSchema, GiftProductSchema, GiftPromotionSettingsSchema
from svc.services.gift.dto import CartBannerModel, GiftProductModel, GiftPromotionSettingsModel
from svc.services.gift.gift_mapper import CartBannerMapper, GiftProductMapper, GiftPromotionSettingsMapper
from svc.settings import Settings, get_service_settings

logger = logging.getLogger(__name__)


class GiftManager:
    def __init__(
        self,
        connection: AsyncConnection = Depends(database.connection),
        config: Settings = Depends(get_service_settings),
    ):
        self._connection = connection
        self._config = config

    async def get_active_gift_promotion_settings(self, warehouse_id: UUID) -> Optional[GiftPromotionSettingsModel]:
        dt = datetime.utcnow()
        query = GiftPromotionSettingsSchema.table.select().where(
            GiftPromotionSettingsSchema.warehouse_id == warehouse_id,
            GiftPromotionSettingsSchema.active.is_(True),
            GiftPromotionSettingsSchema.date_from < dt,
            GiftPromotionSettingsSchema.date_till > dt,
        )
        entity = (await self._connection.execute(query)).first()
        if entity is None:
            return None

        return GiftPromotionSettingsMapper.map_to_model(entity)

    async def get_gift_product(self, settings_id: int) -> Optional[GiftProductModel]:
        query = GiftProductSchema.table.select().where(GiftProductSchema.gift_promotion_settings_id == settings_id)
        entity = (await self._connection.execute(query)).first()
        if entity is None:
            return None

        return GiftProductMapper.map_to_model(entity)

    async def get_banner(self, banner_id: int) -> Optional[CartBannerModel]:
        query = CartBannerSchema.table.select().where(CartBannerSchema.id == banner_id)
        entity = (await self._connection.execute(query)).first()
        if entity is None:
            return None

        return CartBannerMapper.map_to_model(entity)
