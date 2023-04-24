from typing import Optional

from fastapi import Depends

from svc.api.models.conditions import ProgressBar
from svc.persist.dao.fee import Fee
from svc.services.conditions.bonus_bar_manager import BonusProgressBarManager
from svc.services.conditions.bonus_manager import OrderBonus
from svc.services.conditions.fee_bar_manager import FeeProgressBarManager
from svc.services.conditions.happy_hours_bar_manager import HappyHoursProgressBarManager


class BarManager:
    def __init__(
        self,
        fee_bar_manager: FeeProgressBarManager = Depends(FeeProgressBarManager),
        bonus_bar_manager: BonusProgressBarManager = Depends(BonusProgressBarManager),
        happy_hours_bar_manager: HappyHoursProgressBarManager = Depends(HappyHoursProgressBarManager),
    ):
        self._fee_bar_manager = fee_bar_manager
        self._bonus_bar_manager = bonus_bar_manager
        self._happy_hours_bar_manager = happy_hours_bar_manager

    def get_catalog_bar(
        self,
        fee: Optional[Fee],
        bonus: Optional[OrderBonus],
        fee_subtotal: int,
        bonus_subtotal: int,
        user_orders_count: int,
    ) -> Optional[ProgressBar]:
        if not bonus and fee:
            return self._fee_bar_manager.get_fee_catalog_bar(fee, fee_subtotal)

        if bonus and not fee:
            if bonus.is_increased:
                return self._happy_hours_bar_manager.get_bonus_catalog_bar(bonus, bonus_subtotal)
            else:
                return self._bonus_bar_manager.get_bonus_catalog_bar(bonus, bonus_subtotal)

        if bonus and fee:
            if bonus.is_increased:
                return self._happy_hours_bar_manager.get_fee_catalog_bar(
                    fee=fee,
                    bonus=bonus,
                    fee_subtotal=fee_subtotal,
                    bonus_subtotal=bonus_subtotal,
                    user_orders_count=user_orders_count,
                )
            else:
                return self._bonus_bar_manager.get_fee_catalog_bar(
                    fee=fee,
                    bonus=bonus,
                    fee_subtotal=fee_subtotal,
                    bonus_subtotal=bonus_subtotal,
                    user_orders_count=user_orders_count,
                )

        return None

    def get_cart_bar(
        self,
        fee: Optional[Fee],
        bonus: Optional[OrderBonus],
        fee_subtotal: int,
        bonus_subtotal: int,
        user_orders_count: int,
    ) -> Optional[ProgressBar]:
        if not bonus and fee:
            return self._fee_bar_manager.get_fee_cart_bar(fee, fee_subtotal)

        if bonus and not fee:
            if bonus.is_increased:
                return self._happy_hours_bar_manager.get_bonus_cart_bar(bonus, bonus_subtotal)
            else:
                return self._bonus_bar_manager.get_bonus_cart_bar(bonus, bonus_subtotal)

        if bonus and fee:
            if bonus.is_increased:
                return self._happy_hours_bar_manager.get_fee_cart_bar(
                    fee=fee,
                    bonus=bonus,
                    fee_subtotal=fee_subtotal,
                    bonus_subtotal=bonus_subtotal,
                    user_orders_count=user_orders_count,
                )
            else:
                return self._bonus_bar_manager.get_fee_cart_bar(
                    fee=fee,
                    bonus=bonus,
                    fee_subtotal=fee_subtotal,
                    bonus_subtotal=bonus_subtotal,
                    user_orders_count=user_orders_count,
                )

        return None
