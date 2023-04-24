from fastapi import APIRouter, Depends

from svc.api.models.base_model import ApiResponse
from svc.api.models.conditions import GetOrderConditionsRequest, OrderConditionsResponse
from svc.services.conditions.order_conditions_service import OrderConditionsService

router = APIRouter(prefix="/orders")


@router.post("/conditions/calculate", response_model=ApiResponse[OrderConditionsResponse])
async def calculate_order_conditions(
    request: GetOrderConditionsRequest,
    service: OrderConditionsService = Depends(OrderConditionsService),
) -> ApiResponse[OrderConditionsResponse]:
    result = await service.get_order_conditions(request)
    return ApiResponse(result=result)
