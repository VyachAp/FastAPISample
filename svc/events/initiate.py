from sqlalchemy.ext.asyncio import AsyncConnection

from svc.services.coupon.coupon_manager import CouponManager
from svc.services.coupon.coupon_service import CouponService
from svc.services.gift.gift_manager import GiftManager
from svc.services.uow import UnitOfWork
from svc.settings import get_service_settings


def create_coupon_service(connection: AsyncConnection) -> CouponService:
    return CouponService(
        coupon_manager=CouponManager(
            connection=connection,
            config=get_service_settings(),
        ),
        gift_manager=GiftManager(
            connection=connection,
            config=get_service_settings(),
        ),
        config=get_service_settings(),
        uow=UnitOfWork(
            connection=connection,
        ),
    )
