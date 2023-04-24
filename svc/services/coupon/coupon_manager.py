import logging
import random
import string
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Set
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import func as sqla_func
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.api.models.coupon import CouponKind, CouponOrderItem
from svc.persist.database import database
from svc.persist.schemas.coupon import (
    CouponPermitCategorySchema,
    CouponPermitUserSchema,
    CouponPermitWarehouseSchema,
    CouponSchema,
    CouponTypeDb,
    CouponValueOrderNumberSchema,
    UserCouponSchema,
)
from svc.services.coupon.coupon_mapper import CouponMapper
from svc.services.coupon.dto import CouponModel, UserCouponModel
from svc.settings import Settings, get_service_settings
from svc.utils.money import cents_to_dollars

logger = logging.getLogger(__name__)


class CouponManager:
    _coupon_columns = [
        CouponSchema.id,
        CouponSchema.active,
        CouponSchema.name,
        CouponSchema.description,
        CouponSchema.value,
        CouponSchema.kind,
        CouponSchema.valid_till,
        CouponSchema.quantity,
        CouponSchema.limit,
        CouponSchema.minimum_order_amount,
        CouponSchema.created_at,
        CouponSchema.updated_at,
        CouponSchema.user_id,
        CouponSchema.token,
        CouponSchema.coupon_type,
        CouponSchema.orders_from,
        CouponSchema.orders_to,
        CouponSchema.referral_active,
        CouponSchema.max_discount,
    ]

    def __init__(
        self,
        connection: AsyncConnection = Depends(database.connection),
        config: Settings = Depends(get_service_settings),
    ):
        self._connection = connection
        self._config = config

    def get_coupon_name(self, size: int = 6, chars: str = string.ascii_uppercase + string.digits) -> str:
        return "".join(random.SystemRandom().choice(chars) for _ in range(size))

    def is_max_discount_exceeded(self, coupon: CouponModel, calculated_discount: int) -> bool:
        if coupon.kind != CouponKind.percent:
            return False

        if coupon.max_discount is None:
            return False

        if calculated_discount <= coupon.max_discount:
            return False

        return True

    def get_coupon_discount(
        self,
        coupon: CouponModel,
        order_subtotal: int,
    ) -> int:
        coupon_id = coupon.id
        if order_subtotal <= 0:
            logger.error(
                f"[coupon_id={coupon_id}] Order.subtotal must be > 0",
            )
            return 0

        if coupon.kind == CouponKind.percent:
            factor = Decimal(coupon.value) / 100
            discount = int((order_subtotal * factor).to_integral_value(ROUND_HALF_UP))
        else:
            discount = coupon.value

        if order_subtotal - discount < self._config.min_order_amount:
            max_discount = max(order_subtotal - self._config.min_order_amount, 0)
            logger.debug(
                f"[coupon_id={coupon_id}, order_subtotal={order_subtotal}] "
                f"Coupon without minimum amount with discount={discount} cents that >= {order_subtotal} cents found. "
                f"Coupon_discount={max_discount} cents"
            )
            discount = max_discount

        return discount

    async def overwrite_coupon_value(self, coupon: CouponModel, delivered_orders_count: int) -> None:
        current_number = delivered_orders_count + 1
        select_statement = (
            select(CouponValueOrderNumberSchema.coupon_value)
            .select_from(CouponValueOrderNumberSchema.table)
            .where(CouponValueOrderNumberSchema.coupon_id == coupon.id)
            .where(CouponValueOrderNumberSchema.orders_number == current_number)
        )
        entity = (await self._connection.execute(select_statement)).first()
        if entity is not None:
            old_coupon_value = coupon.value
            coupon.value = CouponMapper.calculate_value(
                value=entity[CouponValueOrderNumberSchema.coupon_value],
                kind=coupon.kind,
            )
            logger.info(
                f"[coupon_id={coupon.id}, old_coupon_value={old_coupon_value}, new_coupon_value={coupon.value}]"
                f"Coupon_value got overwritten."
            )

    async def get_coupon(self, coupon_id: UUID) -> Optional[CouponModel]:
        from_statement = CouponSchema.table
        select_statement = select(self._coupon_columns).select_from(from_statement).where(CouponSchema.id == coupon_id)
        entity = (await self._connection.execute(select_statement)).first()
        if entity is None:
            return None

        return CouponMapper.map_to_model(entity)

    async def get_current_order_coupon(self, order_id: UUID) -> Optional[CouponModel]:
        join_statement = CouponSchema.table.join(UserCouponSchema.table, CouponSchema.id == UserCouponSchema.coupon_id)
        select_statement = (
            select(self._coupon_columns)
            .select_from(join_statement)
            .where(UserCouponSchema.order_id == order_id)
            .order_by(UserCouponSchema.updated_at.desc())
        )
        entity = (await self._connection.execute(select_statement)).first()
        if entity is None:
            return None

        return CouponMapper.map_to_model(entity)

    async def create_referral_coupon(self, coupon_name: str, user_id: UUID) -> CouponModel:
        coupon_kind = CouponKind.from_db_type(self._config.referral_coupon.kind)
        if coupon_kind == CouponKind.fixed:
            value = cents_to_dollars(self._config.referral_coupon.value)
        else:
            value = Decimal(self._config.referral_coupon.value)

        insert_values = {
            CouponSchema.id: uuid4(),
            CouponSchema.name: coupon_name,
            CouponSchema.user_id: user_id,
            CouponSchema.coupon_type: CouponTypeDb.referral,
            CouponSchema.kind: self._config.referral_coupon.kind,
            CouponSchema.quantity: self._config.referral_coupon.quantity,
            CouponSchema.limit: self._config.referral_coupon.limit,
            CouponSchema.value: value,
            CouponSchema.minimum_order_amount: cents_to_dollars(self._config.referral_coupon.minimum_order_amount),
            CouponSchema.created_at: datetime.now(timezone.utc),
            CouponSchema.updated_at: datetime.now(timezone.utc),
            CouponSchema.orders_to: self._config.referral_coupon.initial_orders_count_permit,
            CouponSchema.referral_active: True,
            CouponSchema.max_discount: cents_to_dollars(self._config.referral_coupon.max_discount),
        }

        query = CouponSchema.table.insert().values(insert_values).returning(CouponSchema.table)
        entity = (await self._connection.execute(query)).first()

        if entity is None:
            raise RuntimeError(f"Error inserting coupon name={coupon_name}, user_id={user_id}")

        return CouponMapper.map_to_model(entity)

    async def create_user_coupon(
        self,
        coupon_id: UUID,
        user_id: UUID,
        order_id: UUID,
        order_paid: bool,
    ) -> UserCouponModel:
        query = (
            UserCouponSchema.table.insert()
            .values(
                id=uuid4(),
                coupon_id=coupon_id,
                user_id=user_id,
                order_id=order_id,
                order_paid=order_paid,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            .returning(UserCouponSchema.table)
        )
        entity = (await self._connection.execute(query)).first()

        return UserCouponModel(
            id=entity[UserCouponSchema.id],  # type: ignore
            user_id=entity[UserCouponSchema.user_id],  # type: ignore
            coupon_id=entity[UserCouponSchema.coupon_id],  # type: ignore
            order_id=entity[UserCouponSchema.order_id],  # type: ignore
            order_paid=entity[UserCouponSchema.order_paid],  # type: ignore
            created_at=entity[UserCouponSchema.created_at],  # type: ignore
            updated_at=entity[UserCouponSchema.updated_at],  # type: ignore
        )

    async def user_coupon_set_order_paid(self, coupon_id: UUID, order_id: UUID) -> None:
        update_values = {
            UserCouponSchema.order_paid: True,
            UserCouponSchema.updated_at: datetime.now(timezone.utc),
        }
        update_statement = (
            UserCouponSchema.table.update()
            .where(UserCouponSchema.coupon_id == coupon_id)
            .where(UserCouponSchema.order_id == order_id)
            .values(update_values)
        )
        await self._connection.execute(update_statement)

    async def delete_user_coupon(self, coupon_id: UUID, order_id: UUID) -> None:
        query = (
            UserCouponSchema.table.delete()
            .where(UserCouponSchema.coupon_id == coupon_id)
            .where(UserCouponSchema.order_id == order_id)
        )
        await self._connection.execute(query)

    async def increment_coupon_quantity(self, coupon_id: UUID) -> None:
        update_values = {
            CouponSchema.quantity: CouponSchema.quantity + 1,
            CouponSchema.updated_at: datetime.now(timezone.utc),
        }
        update_statement = CouponSchema.table.update().where(CouponSchema.id == coupon_id).values(update_values)
        await self._connection.execute(update_statement)

    async def decrement_coupon_quantity(self, coupon_id: UUID) -> None:
        update_values = {
            CouponSchema.quantity: CouponSchema.quantity - 1,
            CouponSchema.updated_at: datetime.now(timezone.utc),
        }
        update_statement = CouponSchema.table.update().where(CouponSchema.id == coupon_id).values(update_values)
        await self._connection.execute(update_statement)

    async def is_coupon_name_taken(self, coupon_name: str) -> bool:
        from_statement = CouponSchema.table
        select_statement = (
            select(self._coupon_columns)
            .select_from(from_statement)
            .where(CouponSchema.name == coupon_name)
            .where(CouponSchema.active.is_(True))
        )
        entity = (await self._connection.execute(select_statement)).first()

        return entity is not None

    async def get_active_referral_coupon(self, user_id: UUID) -> Optional[CouponModel]:
        from_statement = CouponSchema.table
        select_statement = (
            select(self._coupon_columns)
            .select_from(from_statement)
            .where(CouponSchema.user_id == user_id)
            .where(CouponSchema.referral_active.is_(True))
            .order_by(CouponSchema.updated_at.desc())
        )
        entity = (await self._connection.execute(select_statement)).first()
        if entity is None:
            return None

        return CouponMapper.map_to_model(entity)

    async def get_active_coupon_by_name(self, name: str) -> Optional[CouponModel]:
        from_statement = CouponSchema.table
        select_statement = (
            select(self._coupon_columns)
            .select_from(from_statement)
            .where(CouponSchema.name == name)
            .where(CouponSchema.active.is_(True))
            .where(or_(CouponSchema.valid_till.is_(None), CouponSchema.valid_till > datetime.utcnow()))
        )
        entity = (await self._connection.execute(select_statement)).first()
        if entity is None:
            return None

        return CouponMapper.map_to_model(entity)

    async def get_user_coupon_usage_count(self, user_id: UUID, coupon_id: UUID) -> int:
        columns = [
            sqla_func.count(UserCouponSchema.id).label("usage_count"),
        ]
        from_statement = UserCouponSchema.table
        select_statement = (
            select(columns)
            .select_from(from_statement)
            .where(UserCouponSchema.user_id == user_id)
            .where(UserCouponSchema.coupon_id == coupon_id)
            .where(UserCouponSchema.order_paid.is_(True))
        )
        entity = (await self._connection.execute(select_statement)).first()

        return entity["usage_count"]  # type: ignore

    async def is_permitted_user(self, user_id: UUID, coupon_id: UUID) -> bool:
        select_statement = (
            select(CouponPermitUserSchema.id)
            .select_from(CouponPermitUserSchema.table)
            .where(CouponPermitUserSchema.coupon_id == coupon_id)
        )
        entity = (await self._connection.execute(select_statement)).first()
        if entity is None:
            return True

        select_statement = select_statement.where(CouponPermitUserSchema.user_id == user_id)
        entity = (await self._connection.execute(select_statement)).one_or_none()
        if entity is not None:
            return True

        return False

    async def is_permitted_warehouse(self, warehouse_id: UUID, coupon_id: UUID) -> bool:
        select_statement = (
            select(CouponPermitWarehouseSchema.warehouse_id)
            .select_from(CouponPermitWarehouseSchema.table)
            .where(CouponPermitWarehouseSchema.coupon_id == coupon_id)
        )
        entity = (await self._connection.execute(select_statement)).first()
        if entity is None:
            return True

        select_statement = select_statement.where(CouponPermitWarehouseSchema.warehouse_id == warehouse_id)
        entity = (await self._connection.execute(select_statement)).one_or_none()
        if entity is not None:
            return True

        return False

    def filter_items_for_permitted_categories(
        self,
        order_items: List[CouponOrderItem],
        categories_ids: Set[UUID],
    ) -> List[CouponOrderItem]:
        items_for_discount = [it for it in order_items if categories_ids.intersection(it.categories_ids)]
        logger.info(
            f"[product_ids=[{', '.join(str(it) for it in items_for_discount)}]] "
            f"Coupon is applicable for these products.",
        )
        return items_for_discount

    async def get_permitted_categories_ids(self, coupon_id: UUID) -> Set[UUID]:
        select_statement = (
            select(CouponPermitCategorySchema.category_id)
            .select_from(CouponPermitCategorySchema.table)
            .where(CouponPermitCategorySchema.coupon_id == coupon_id)
        )
        entities = (await self._connection.execute(select_statement)).all()

        return {it["category_id"] for it in entities}
