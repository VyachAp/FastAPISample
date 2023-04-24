from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from fastapi import Depends
from pytz import timezone

from svc.api.models.conditions import DeliveryMode
from svc.api.models.coupon import DistributedDiscountItemShort
from svc.api.models.order import OrderItem
from svc.infrastructure.warehouse.models import WarehouseShortModel
from svc.persist.dao.bonus import BonusDAO
from svc.persist.dao.happy_hours import HappyHoursDAO
from svc.utils.discounting import calculate_order_distributed_discount


@dataclass
class OrderBonus:
    bonus_amount: int
    applied_bonus: int
    required_subtotal: int
    is_increased: bool
    bonus_percent: Optional[int]
    discounted_items: List[DistributedDiscountItemShort]

    @property
    def bonus_pretty(self) -> str:
        return f"{self.bonus_percent}%" if self.bonus_percent else "${bonus:4.2f}".format(bonus=self.bonus_amount / 100)


class OrderBonusManager:
    def __init__(
        self,
        bonus_dao: BonusDAO = Depends(BonusDAO),
        happy_hours_dao: HappyHoursDAO = Depends(HappyHoursDAO),
    ) -> None:
        self._bonus_dao = bonus_dao
        self._happy_hours_dao = happy_hours_dao

    async def get_scheduled_happy_hours_bonus(self, warehouse: WarehouseShortModel) -> Optional[int]:
        happy_hours = await self._happy_hours_dao.get_active_scheduled_happy_hours(warehouse.id)
        if not happy_hours:
            return None

        warehouse_now = datetime.now(tz=timezone(warehouse.tz))
        weekday = warehouse_now.weekday()
        warehouse_now_time = warehouse_now.time()
        yesterday = (weekday - 1) % 7
        yesterday_happy_hours = (it for it in happy_hours if it.weekday == yesterday and it.start_time > it.end_time)
        for hh in yesterday_happy_hours:
            if hh.end_time >= warehouse_now_time:
                return hh.value

        weekday_happy_hours = (it for it in happy_hours if it.weekday == weekday)
        for hh in weekday_happy_hours:
            if hh.start_time < hh.end_time and hh.start_time <= warehouse_now_time <= hh.end_time:
                return hh.value
            if hh.start_time > hh.end_time and hh.start_time < warehouse_now_time:
                return hh.value

        return None

    async def calculate_order_bonus(
        self,
        warehouse: WarehouseShortModel,
        order_subtotal: int,
        delivery_mode: DeliveryMode,
        order_items: Iterable[OrderItem],
        purchase_prices_mapper: Dict[UUID, int],
    ) -> Optional[OrderBonus]:
        warehouse_bonus = await self._bonus_dao.get_warehouse_bonus_settings(warehouse.id)
        if not warehouse_bonus:
            return None

        if delivery_mode == DeliveryMode.surge:
            happy_hours_bonus = None
        else:
            happy_hours_bonus = await self._happy_hours_dao.get_forced_happy_hours_bonus(warehouse.id, warehouse.tz)
            if happy_hours_bonus is None:
                happy_hours_bonus = await self.get_scheduled_happy_hours_bonus(warehouse)

        if happy_hours_bonus is None and warehouse_bonus.happy_hours_only:
            return None

        if warehouse_bonus.happy_hours_only and happy_hours_bonus:
            bonus_amount = happy_hours_bonus
            bonus_percent = happy_hours_bonus if warehouse_bonus.bonus_percent else None
            if warehouse_bonus.bonus_percent:
                applied_bonus = (
                    int(order_subtotal * happy_hours_bonus / 100)
                    if order_subtotal >= warehouse_bonus.required_subtotal
                    else 0
                )
            else:
                applied_bonus = happy_hours_bonus if order_subtotal >= warehouse_bonus.required_subtotal else 0
            is_bonus_increased = True

        elif warehouse_bonus.bonus_fixed:
            bonus_amount = max(warehouse_bonus.bonus_fixed, happy_hours_bonus or 0)
            applied_bonus = bonus_amount if order_subtotal >= warehouse_bonus.required_subtotal else 0
            bonus_percent = None
            is_bonus_increased = (happy_hours_bonus or 0) > warehouse_bonus.bonus_fixed

        else:
            bonus_percent = max(warehouse_bonus.bonus_percent or 0, happy_hours_bonus or 0)
            applied_bonus = (
                int(order_subtotal * bonus_percent / 100) if order_subtotal >= warehouse_bonus.required_subtotal else 0
            )
            bonus_amount = bonus_percent
            is_bonus_increased = (happy_hours_bonus or 0) > warehouse_bonus.bonus_percent

        bonus = calculate_order_distributed_discount(
            discount_value=applied_bonus,
            order_items=order_items,
            purchase_prices_mapper=purchase_prices_mapper,
        )

        return OrderBonus(
            bonus_amount=bonus_amount,
            applied_bonus=bonus.value,
            required_subtotal=warehouse_bonus.required_subtotal,
            bonus_percent=bonus_percent,
            is_increased=is_bonus_increased,
            discounted_items=bonus.items,
        )
