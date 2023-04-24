from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.database import conditions_database
from svc.persist.schemas.fee import FeeSchema, FeeType, UserFeeSchema, WarehouseFeeSchema


@dataclass
class Fee:
    id: UUID
    name: str
    description: str
    value: int
    image: Optional[str]
    fee_type: FeeType
    fee_amount: int
    free_after_subtotal: Optional[int]


class FeeDAO:
    def __init__(self, connection: AsyncConnection = Depends(conditions_database.connection)):
        self._connection = connection

    async def get_applicable_fees(self, user_id: UUID, warehouse_id: UUID) -> List[Fee]:
        columns = [
            FeeSchema.id.distinct(),
            FeeSchema.name,
            FeeSchema.description,
            FeeSchema.value,
            FeeSchema.img_url,
            FeeSchema.fee_type,
            FeeSchema.free_after_subtotal,
        ]

        from_statement = FeeSchema.table.outerjoin(UserFeeSchema.table, FeeSchema.id == UserFeeSchema.fee_id).outerjoin(
            WarehouseFeeSchema.table, FeeSchema.id == WarehouseFeeSchema.fee_id
        )
        user_warehouse_condition = or_(
            or_(FeeSchema.active.is_(True), UserFeeSchema.user_id == user_id),
            WarehouseFeeSchema.warehouse_id == warehouse_id,
        )
        query = select(columns).select_from(from_statement).where(user_warehouse_condition)

        result = (await self._connection.execute(query)).all()

        return [
            Fee(
                id=entity[FeeSchema.id],
                name=entity[FeeSchema.name],
                description=entity[FeeSchema.description],
                value=entity[FeeSchema.value],
                image=entity[FeeSchema.img_url],
                fee_type=entity[FeeSchema.fee_type],
                free_after_subtotal=entity[FeeSchema.free_after_subtotal],
                fee_amount=entity[FeeSchema.value],
            )
            for entity in result
        ]
