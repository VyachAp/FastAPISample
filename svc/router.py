from fastapi import APIRouter

from svc.api.handlers.automation import router as health_router
from svc.api.handlers.bulk import router as bulk_router
from svc.api.handlers.conditions import router as order_conditions_router
from svc.api.handlers.coupon import router as coupon_router
from svc.api.handlers.gift import router as gift_router


def prepare_router(app_router: APIRouter) -> None:
    app_router.include_router(health_router, tags=["automation"])
    app_router.include_router(coupon_router, tags=["coupon"])
    app_router.include_router(order_conditions_router, tags=["order_conditions"])
    app_router.include_router(gift_router, tags=["gift"])
    app_router.include_router(bulk_router, tags=["bulk"])
