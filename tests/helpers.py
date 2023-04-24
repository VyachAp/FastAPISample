from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.schemas.coupon import UserCouponSchema
from svc.services.coupon.coupon_manager import CouponManager
from svc.services.coupon.dto import CouponModel, UserCouponModel
from svc.settings import get_service_settings


async def get_coupon(
    connection: AsyncConnection,
    coupon_id: Optional[UUID] = None,
    name: Optional[str] = None,
) -> Optional[CouponModel]:
    settings = get_service_settings()
    manager = CouponManager(connection, settings)
    if coupon_id:
        return await manager.get_coupon(coupon_id)
    if name:
        return await manager.get_active_coupon_by_name(name)


async def get_user_coupon(
    connection: AsyncConnection,
    *,
    user_coupon_id: Optional[UUID] = None,
    coupon_id: Optional[UUID] = None,
    order_id: Optional[UUID] = None,
) -> Optional[UserCouponModel]:
    columns = [
        UserCouponSchema.id,
        UserCouponSchema.user_id,
        UserCouponSchema.coupon_id,
        UserCouponSchema.order_id,
        UserCouponSchema.order_paid,
        UserCouponSchema.created_at,
        UserCouponSchema.updated_at,
    ]
    from_statement = UserCouponSchema.table
    if user_coupon_id:
        select_statement = select(columns).select_from(from_statement).where(UserCouponSchema.id == user_coupon_id)
    elif coupon_id and order_id:
        select_statement = (
            select(columns)
            .select_from(from_statement)
            .where(UserCouponSchema.coupon_id == coupon_id)
            .where(UserCouponSchema.order_id == order_id)
        )
    else:
        return None

    entity = (await connection.execute(select_statement)).first()
    if entity is None:
        return None

    return UserCouponModel(
        id=entity[UserCouponSchema.id],
        user_id=entity[UserCouponSchema.user_id],
        coupon_id=entity[UserCouponSchema.coupon_id],
        order_id=entity[UserCouponSchema.order_id],
        order_paid=entity[UserCouponSchema.order_paid],
        created_at=entity[UserCouponSchema.created_at],
        updated_at=entity[UserCouponSchema.updated_at],
    )
