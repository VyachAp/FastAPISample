from uuid import UUID

import fastapi
from fastapi import Depends

from svc.api.models.base_model import ApiResponse
from svc.api.models.coupon import (
    AddOrderCouponRequest,
    CouponDetail,
    CreateReferralCouponRequest,
    OrderCouponDetail,
    RecalculateOrderCouponRequest,
)
from svc.services.coupon.coupon_service import CouponService

router = fastapi.APIRouter(prefix="/coupons")


@router.get("/{coupon_id}", response_model=ApiResponse[CouponDetail])
async def get_coupon(
    coupon_id: UUID,
    coupon_service: CouponService = Depends(CouponService),
) -> ApiResponse[CouponDetail]:
    return ApiResponse(result=await coupon_service.get_coupon(coupon_id))


@router.post("/orders/{order_id}", response_model=ApiResponse[OrderCouponDetail])
async def add_order_coupon(
    order_id: UUID,
    request: AddOrderCouponRequest,
    coupon_service: CouponService = Depends(CouponService),
) -> ApiResponse[OrderCouponDetail]:
    return ApiResponse(result=await coupon_service.add_coupon(order_id, request))


@router.post("/{coupon_id}/orders/{order_id}", response_model=ApiResponse[OrderCouponDetail])
async def recalculate_coupon_for_order(
    coupon_id: UUID,
    order_id: UUID,
    request: RecalculateOrderCouponRequest,
    coupon_service: CouponService = Depends(CouponService),
) -> ApiResponse[OrderCouponDetail]:
    return ApiResponse(result=await coupon_service.recalculate_coupon_discount(order_id, coupon_id, request))


@router.delete("/{coupon_id}/orders/{order_id}", response_model=ApiResponse[OrderCouponDetail])
async def delete_order_coupon(
    coupon_id: UUID,
    order_id: UUID,
    coupon_service: CouponService = Depends(CouponService),
) -> ApiResponse[OrderCouponDetail]:
    return ApiResponse(result=await coupon_service.delete_coupon(coupon_id, order_id))


@router.post("/referral", response_model=ApiResponse[str])
async def create_referral_coupon(
    request: CreateReferralCouponRequest,
    coupon_service: CouponService = Depends(CouponService),
) -> ApiResponse[str]:
    return ApiResponse(result=await coupon_service.create_referral_coupon(request))
