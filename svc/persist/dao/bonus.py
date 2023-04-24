from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.database import conditions_database
from svc.persist.schemas.bonus import WarehouseBonusSettingsSchema


@dataclass
class WarehouseBonusSettings:
    required_subtotal: int
    bonus_percent: int
    bonus_fixed: int
    happy_hours_only: bool


class BonusDAO:
    def __init__(self, connection: AsyncConnection = Depends(conditions_database.connection)):
        self._connection = connection

    async def get_warehouse_bonus_settings(self, warehouse_id: UUID) -> Optional[WarehouseBonusSettings]:
        columns = [
            WarehouseBonusSettingsSchema.required_subtotal,
            WarehouseBonusSettingsSchema.bonus_percent,
            WarehouseBonusSettingsSchema.bonus_fixed,
            WarehouseBonusSettingsSchema.happy_hours_only,
        ]

        bonus_query = (
            select(columns)
            .select_from(WarehouseBonusSettingsSchema.table)
            .where(WarehouseBonusSettingsSchema.warehouse_id == warehouse_id)
            .where(WarehouseBonusSettingsSchema.active.is_(True))
        )

        result = (await self._connection.execute(bonus_query)).first()

        if result:
            return WarehouseBonusSettings(
                required_subtotal=result[WarehouseBonusSettingsSchema.required_subtotal],
                bonus_fixed=result[WarehouseBonusSettingsSchema.bonus_fixed],
                bonus_percent=result[WarehouseBonusSettingsSchema.bonus_percent],
                happy_hours_only=result[WarehouseBonusSettingsSchema.happy_hours_only],
            )

        return None
