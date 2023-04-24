import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.dialects.postgresql import Insert as PgInsert
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.api.models.bulk import BulkOperation
from svc.persist.database import database
from svc.persist.schemas.coupon import (
    CouponPermitCategorySchema,
    CouponPermitUserSchema,
    CouponPermitWarehouseSchema,
    CouponSchema,
    CouponValueOrderNumberSchema,
)
from svc.services.bulk.dto import BulkCouponRecord, BulkCouponValueRecord
from svc.utils.money import cents_to_dollars

logger = logging.getLogger(__name__)


class BulkCouponManager:
    def __init__(
        self,
        connection: AsyncConnection = Depends(database.connection),
    ) -> None:
        self._connection = connection

    async def overwrite_warehouses(
        self,
        items: list[BulkCouponRecord],
    ) -> None:
        if not items:
            return

        coupon_ids = list[UUID]()
        ins_values = list[dict[str, Any]]()
        created_at = datetime.now()

        for item in items:
            if item.coupon_id is None:
                continue

            coupon_ids.append(item.coupon_id)

            if not item.valid_warehouses:
                continue

            ins_values.extend(
                {
                    CouponPermitWarehouseSchema.coupon_id.name: item.coupon_id,
                    CouponPermitWarehouseSchema.warehouse_id.name: warehouse_id,
                    CouponPermitWarehouseSchema.created_at.name: created_at,
                }
                for warehouse_id in item.valid_warehouses
            )

        del_stmt = CouponPermitWarehouseSchema.table.delete().where(
            CouponPermitWarehouseSchema.coupon_id.in_(coupon_ids),
        )
        await self._connection.execute(del_stmt)

        if not ins_values:
            return

        stmt = PgInsert(CouponPermitWarehouseSchema.table).values(ins_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                CouponPermitWarehouseSchema.coupon_id,
                CouponPermitWarehouseSchema.warehouse_id,
            ],
            set_={
                CouponPermitWarehouseSchema.created_at.name: stmt.excluded[CouponPermitWarehouseSchema.created_at.name]
            },
        )

        await self._connection.execute(stmt)

    async def overwrite_users(
        self,
        items: list[BulkCouponRecord],
    ) -> None:
        if not items:
            return

        coupon_ids = list[UUID]()
        ins_values = list[dict[str, Any]]()
        created_at = datetime.now()

        for item in items:
            if item.coupon_id is None:
                continue

            coupon_ids.append(item.coupon_id)

            if not item.valid_users:
                continue

            ins_values.extend(
                {
                    CouponPermitUserSchema.coupon_id.name: item.coupon_id,
                    CouponPermitUserSchema.user_id.name: user_id,
                    CouponPermitUserSchema.created_at.name: created_at,
                }
                for user_id in item.valid_users
            )

        del_stmt = CouponPermitUserSchema.table.delete().where(
            CouponPermitUserSchema.coupon_id.in_(coupon_ids),
        )
        await self._connection.execute(del_stmt)

        if not ins_values:
            return

        stmt = PgInsert(CouponPermitUserSchema.table).values(ins_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                CouponPermitUserSchema.coupon_id,
                CouponPermitUserSchema.user_id,
            ],
            set_={CouponPermitUserSchema.created_at.name: stmt.excluded[CouponPermitUserSchema.created_at.name]},
        )
        await self._connection.execute(stmt)

    async def overwrite_categories(
        self,
        items: list[BulkCouponRecord],
    ) -> None:
        if not items:
            return

        coupon_ids = list[UUID]()
        ins_values = list[dict[str, Any]]()
        created_at = datetime.now()

        for item in items:
            if item.coupon_id is None:
                continue

            coupon_ids.append(item.coupon_id)

            if not item.valid_categories:
                continue

            ins_values.extend(
                {
                    CouponPermitCategorySchema.coupon_id.name: item.coupon_id,
                    CouponPermitCategorySchema.category_id.name: category_id,
                    CouponPermitCategorySchema.created_at.name: created_at,
                }
                for category_id in item.valid_categories
            )

        del_stmt = CouponPermitCategorySchema.table.delete().where(
            CouponPermitCategorySchema.coupon_id.in_(coupon_ids),
        )
        await self._connection.execute(del_stmt)

        if not ins_values:
            return

        stmt = PgInsert(CouponPermitCategorySchema.table).values(ins_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                CouponPermitCategorySchema.coupon_id,
                CouponPermitCategorySchema.category_id,
            ],
            set_={
                CouponPermitCategorySchema.created_at.name: stmt.excluded[CouponPermitCategorySchema.created_at.name],
            },
        )
        await self._connection.execute(stmt)

    async def overwrite_coupon_values(self, items: list[BulkCouponValueRecord]) -> None:
        coupon_ids = [item.coupon_id for item in items if item.coupon_id is not None]
        if not coupon_ids:
            return

        del_stmt = CouponValueOrderNumberSchema.table.delete().where(
            CouponValueOrderNumberSchema.coupon_id.in_(coupon_ids)
        )
        await self._connection.execute(del_stmt)

        created_at = datetime.now()
        ins_values = [
            {
                CouponValueOrderNumberSchema.coupon_id.name: item.coupon_id,
                CouponValueOrderNumberSchema.coupon_value.name: cents_to_dollars(item.data.value),
                CouponValueOrderNumberSchema.orders_number.name: item.data.orders_number,
                CouponValueOrderNumberSchema.created_at.name: created_at,
            }
            for item in items
            if item.coupon_id is not None
        ]

        if not ins_values:
            return

        stmt = PgInsert(CouponValueOrderNumberSchema.table).values(ins_values)

        stmt = stmt.on_conflict_do_update(
            index_elements=[
                CouponValueOrderNumberSchema.coupon_id,
                CouponValueOrderNumberSchema.orders_number,
            ],
            set_={
                CouponValueOrderNumberSchema.coupon_value.name: stmt.excluded[
                    CouponValueOrderNumberSchema.coupon_value.name
                ],
                CouponValueOrderNumberSchema.created_at.name: stmt.excluded[
                    CouponValueOrderNumberSchema.created_at.name
                ],
            },
        )
        await self._connection.execute(stmt)
        for item in items:
            item.applied_at = created_at

    async def bulk_upsert(
        self,
        items: list[BulkCouponRecord],
    ) -> None:
        if not items:
            return

        ins_values = list[dict[str, Any]]()
        applied_at = datetime.now()
        items_map = dict[str, BulkCouponRecord]()

        for item in items:
            item.coupon_id = uuid4()
            item.applied_at = applied_at
            items_map[item.data.name.lower()] = item
            ins_values.append(
                {
                    CouponSchema.id.name: item.coupon_id,
                    CouponSchema.name.name: item.data.name,
                    CouponSchema.active.name: item.data.active,
                    CouponSchema.value.name: cents_to_dollars(item.data.value),
                    CouponSchema.kind.name: item.data.kind.to_db_type(),
                    CouponSchema.quantity.name: item.data.quantity,
                    CouponSchema.limit.name: item.data.limit,
                    CouponSchema.max_discount.name: cents_to_dollars(item.data.max_discount),
                    CouponSchema.valid_till.name: item.data.valid_till,
                    CouponSchema.minimum_order_amount.name: cents_to_dollars(item.data.minimum_order_amount),
                    CouponSchema.orders_from.name: item.data.orders_from,
                    CouponSchema.orders_to.name: item.data.orders_to,
                    CouponSchema.created_at.name: applied_at,
                    CouponSchema.updated_at.name: applied_at,
                }
            )

        stmt = (
            PgInsert(CouponSchema.table)
            .values(ins_values)
            .returning(
                CouponSchema.id,
                CouponSchema.name,
                (CouponSchema.created_at == CouponSchema.updated_at).label("is_new"),
            )
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[CouponSchema.name],
            set_={
                CouponSchema.active.name: stmt.excluded[CouponSchema.active.name],
                CouponSchema.value.name: stmt.excluded[CouponSchema.value.name],
                CouponSchema.kind.name: stmt.excluded[CouponSchema.kind.name],
                CouponSchema.quantity.name: stmt.excluded[CouponSchema.quantity.name],
                CouponSchema.limit.name: stmt.excluded[CouponSchema.limit.name],
                CouponSchema.max_discount.name: stmt.excluded[CouponSchema.max_discount.name],
                CouponSchema.valid_till.name: stmt.excluded[CouponSchema.valid_till.name],
                CouponSchema.minimum_order_amount.name: stmt.excluded[CouponSchema.minimum_order_amount.name],
                CouponSchema.orders_from.name: stmt.excluded[CouponSchema.orders_from.name],
                CouponSchema.orders_to.name: stmt.excluded[CouponSchema.orders_to.name],
                CouponSchema.updated_at.name: stmt.excluded[CouponSchema.updated_at.name],
            },
        )

        entities = await self._connection.execute(stmt)
        coupon_id: UUID
        coupon_name: str
        is_new: bool

        for coupon_id, coupon_name, is_new in entities:
            key: str = coupon_name.lower()
            if (target := items_map.get(key)) is None:
                logger.warning(f"Coupon is not found in source data [{coupon_name=}]")
                continue

            target.operation = BulkOperation.create if is_new else BulkOperation.update
            target.applied_at = applied_at
            target.coupon_id = coupon_id

    async def get_coupons_name_map(
        self,
        coupon_names: list[str],
        *,
        locked: bool = False,
    ) -> dict[str, UUID]:
        if not coupon_names:
            return {}

        stmt = (
            CouponSchema.table.select()
            .with_only_columns(
                CouponSchema.id,
                CouponSchema.name,
            )
            .where(CouponSchema.name.in_(coupon_names))
        )

        if locked:
            stmt = stmt.with_for_update()

        entities = await self._connection.execute(stmt)
        result = dict[str, UUID]()
        for entity in entities:
            name: str = entity[CouponSchema.name]
            result[name.lower()] = entity[CouponSchema.id]

        return result
