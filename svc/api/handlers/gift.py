import fastapi
from fastapi import Depends

from svc.api.models.base_model import ApiResponse
from svc.api.models.gifts import BannerDetails, GetBannerRequest, GetGiftRequest, GiftDetails
from svc.services.gift.gift_service import GiftService

router = fastapi.APIRouter()


@router.post("/gifts", response_model=ApiResponse[GiftDetails])
async def get_gift_choices(
    request: GetGiftRequest,
    gift_service: GiftService = Depends(GiftService),
) -> ApiResponse[GiftDetails]:
    return ApiResponse(result=await gift_service.get_current_gift(request))


@router.post("/banner", response_model=ApiResponse[BannerDetails])
async def get_banner(
    request: GetBannerRequest,
    gift_service: GiftService = Depends(GiftService),
) -> ApiResponse[BannerDetails]:
    return ApiResponse(result=await gift_service.get_banner(request))
