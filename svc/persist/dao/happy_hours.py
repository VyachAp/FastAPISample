from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from fastapi import Depends
from pytz import timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.database import conditions_database
from svc.persist.schemas.happy_hours import (
    WarehouseForcedHappyHoursSchema,
    WarehouseHappyHoursScheduleSchema,
    WarehouseHappyHoursSettingsSchema,
)


@dataclass
class HappyHoursDto:
    warehouse_id: UUID
    weekday: int
    start_time: time
    end_time: time
    active: bool
    value: int


@dataclass
class ManualHappyHoursDto:
    warehouse_id: UUID
    start_time: datetime
    end_time: datetime
    value: int


class HappyHoursDAO:
    def __init__(self, connection: AsyncConnection = Depends(conditions_database.connection)):
        self._connection = connection

    async def get_forced_happy_hours_bonus(self, warehouse_id: UUID, warehouse_tz: str) -> Optional[int]:
        current_time = datetime.now(tz=timezone(warehouse_tz)).replace(tzinfo=None)
        from_statement = WarehouseHappyHoursSettingsSchema.table.join(
            WarehouseForcedHappyHoursSchema.table,
            WarehouseHappyHoursSettingsSchema.warehouse_id == WarehouseForcedHappyHoursSchema.warehouse_id,
        )
        forced_bonus_query = (
            select([WarehouseHappyHoursSettingsSchema.bonus_amount])
            .select_from(from_statement)
            .where(WarehouseForcedHappyHoursSchema.warehouse_id == warehouse_id)
            .where(WarehouseForcedHappyHoursSchema.start_time <= current_time)
            .where(WarehouseForcedHappyHoursSchema.end_time > current_time)
        )

        forced_bonus = (await self._connection.execute(forced_bonus_query)).first()

        if forced_bonus:
            return forced_bonus[WarehouseHappyHoursSettingsSchema.bonus_amount]

        return None

    async def get_active_scheduled_happy_hours(self, warehouse_id: UUID) -> List[HappyHoursDto]:
        from_statement = WarehouseHappyHoursSettingsSchema.table.join(
            WarehouseHappyHoursScheduleSchema.table,
            WarehouseHappyHoursSettingsSchema.warehouse_id == WarehouseHappyHoursScheduleSchema.warehouse_id,
        )
        columns = [
            WarehouseHappyHoursSettingsSchema.bonus_amount,
            WarehouseHappyHoursScheduleSchema.weekday,
            WarehouseHappyHoursScheduleSchema.start_time,
            WarehouseHappyHoursScheduleSchema.end_time,
            WarehouseHappyHoursScheduleSchema.active,
        ]
        scheduled_bonus_query = (
            select(columns)
            .select_from(from_statement)
            .where(WarehouseHappyHoursScheduleSchema.warehouse_id == warehouse_id)
            .where(WarehouseHappyHoursScheduleSchema.active.is_(True))
        )

        cursor = await self._connection.execute(scheduled_bonus_query)

        return [
            HappyHoursDto(
                warehouse_id=warehouse_id,
                weekday=it[WarehouseHappyHoursScheduleSchema.weekday],
                start_time=it[WarehouseHappyHoursScheduleSchema.start_time],
                end_time=it[WarehouseHappyHoursScheduleSchema.end_time],
                value=it[WarehouseHappyHoursSettingsSchema.bonus_amount],
                active=it[WarehouseHappyHoursScheduleSchema.active],
            )
            for it in cursor
        ]
