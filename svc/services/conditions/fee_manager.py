from typing import List
from uuid import UUID

from fastapi import Depends

from svc.persist.dao.fee import Fee, FeeDAO
from svc.persist.schemas.fee import FeeType
from svc.settings import Settings, get_service_settings


class FeeManager:
    def __init__(
        self,
        fee_dao: FeeDAO = Depends(FeeDAO),
        settings: Settings = Depends(get_service_settings),
    ):
        self._fee_dao = fee_dao
        self._settings = settings.order_bonus_settings

    async def calculate_fees(
        self,
        user_id: UUID,
        warehouse_id: UUID,
        user_orders_count: int,
        order_subtotal: int,
    ) -> List[Fee]:
        fees = await self._fee_dao.get_applicable_fees(user_id, warehouse_id)

        for fee in fees:
            if self._is_small_order_ignored(fee, order_subtotal, user_orders_count):
                fee.value = 0

        return fees

    def _is_small_order_ignored(self, fee: Fee, order_subtotal: int, user_orders_count: int) -> bool:
        return bool(
            fee.fee_type == FeeType.small_order
            and (
                user_orders_count < self._settings.max_free_small_orders
                or (fee.free_after_subtotal and order_subtotal >= fee.free_after_subtotal)
            )
        )
