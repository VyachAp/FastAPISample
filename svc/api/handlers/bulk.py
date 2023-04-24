from fastapi import APIRouter, Depends

from svc.api.models.base_model import ApiResponse
from svc.api.models.bulk import BulkCouponRequest, BulkCouponValueRequest, BulkResponse
from svc.services.bulk.bulk_coupon_service import BulkCouponService

router = APIRouter(prefix="/bulk")


@router.post("/coupons", response_model=ApiResponse[BulkResponse])
async def bulk_upload_coupons(
    bulk_request: BulkCouponRequest,
    bulk_service: BulkCouponService = Depends(BulkCouponService),
) -> ApiResponse[BulkResponse]:
    bulk_result = await bulk_service.save_coupons(bulk_request.items)

    return ApiResponse[BulkResponse](
        result=BulkResponse(items=bulk_result),
    )


@router.post("/coupons/values", response_model=ApiResponse[BulkResponse])
async def bulk_upload_coupon_values(
    bulk_request: BulkCouponValueRequest,
    bulk_service: BulkCouponService = Depends(BulkCouponService),
) -> ApiResponse[BulkResponse]:
    bulk_result = await bulk_service.save_coupon_values(bulk_request.items)

    return ApiResponse[BulkResponse](
        result=BulkResponse(items=bulk_result),
    )
