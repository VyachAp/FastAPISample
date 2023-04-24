from typing import Optional

from fastapi import Depends

from svc.api.models.conditions import OrderConditions, OrderConditionsItem
from svc.persist.dao.fee import Fee
from svc.services.conditions.bonus_manager import OrderBonus
from svc.settings import Settings, get_service_settings


class ConditionsManager:
    def __init__(self, settings: Settings = Depends(get_service_settings)):
        self._bonus_settings = settings.order_bonus_settings
        self._conditions_settings = settings.order_conditions_settings

    def get_order_conditions(
        self,
        fee: Optional[Fee],
        bonus: Optional[OrderBonus],
        user_orders_count: int,
    ) -> Optional[OrderConditions]:
        if fee and bonus:
            if user_orders_count < self._bonus_settings.max_free_small_orders:
                return OrderConditions(
                    image=self._conditions_settings.order_conditions_image,
                    items=[
                        OrderConditionsItem(
                            title=self._conditions_settings.conditions_bonus_title.format(
                                bonus_amount=bonus.bonus_pretty,
                                required_amount=bonus.required_subtotal / 100,
                            ),
                            subtitle=self._conditions_settings.conditions_bonus_subtitle,
                            image=self._conditions_settings.conditions_bonus_image,
                            color=None,
                        )
                    ],
                )
            else:
                return OrderConditions(
                    image=self._conditions_settings.order_conditions_image,
                    items=[
                        OrderConditionsItem(
                            title=self._conditions_settings.conditions_small_order_fee_title.format(
                                required_amount=(fee.free_after_subtotal or 0) / 100,
                            ),
                            subtitle=self._conditions_settings.conditions_small_order_fee_subtitle.format(
                                fee_amount=fee.fee_amount / 100,
                            ),
                            image=self._conditions_settings.conditions_delivery_image,
                            color=None,
                        ),
                        OrderConditionsItem(
                            title=self._conditions_settings.conditions_bonus_title.format(
                                bonus_amount=bonus.bonus_pretty,
                                required_amount=bonus.required_subtotal / 100,
                            ),
                            subtitle=self._conditions_settings.conditions_bonus_subtitle,
                            image=self._conditions_settings.conditions_bonus_image,
                            color=None,
                        ),
                    ],
                )
        elif fee and not bonus:
            if user_orders_count < self._bonus_settings.max_free_small_orders:
                return None
            else:
                return OrderConditions(
                    image=self._conditions_settings.order_conditions_image,
                    items=[
                        OrderConditionsItem(
                            title=self._conditions_settings.conditions_small_order_fee_title.format(
                                required_amount=(fee.free_after_subtotal or 0) / 100,
                            ),
                            subtitle=self._conditions_settings.conditions_small_order_fee_subtitle.format(
                                fee_amount=fee.fee_amount / 100,
                            ),
                            image=self._conditions_settings.conditions_delivery_image,
                            color=None,
                        )
                    ],
                )
        elif bonus:
            return OrderConditions(
                image=self._conditions_settings.order_conditions_image,
                items=[
                    OrderConditionsItem(
                        title=self._conditions_settings.conditions_bonus_title.format(
                            bonus_amount=bonus.bonus_pretty,
                            required_amount=bonus.required_subtotal / 100,
                        ),
                        subtitle=self._conditions_settings.conditions_bonus_subtitle,
                        image=self._conditions_settings.conditions_bonus_image,
                        color=None,
                    )
                ],
            )
        else:
            return None
