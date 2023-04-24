from typing import Optional

from fastapi import Depends

from svc.api.models.conditions import PlaceholderItem, ProgressBar, ProgressBarItem, ProgressBarItemType
from svc.persist.dao.fee import Fee
from svc.settings import Settings, get_service_settings


class FeeProgressBarManager:
    def __init__(self, settings: Settings = Depends(get_service_settings)):
        self._bonus_settings = settings.order_bonus_settings

    def get_fee_catalog_bar(self, fee: Fee, current_subtotal: int) -> Optional[ProgressBar]:
        if fee.value == 0:
            return None

        if current_subtotal == 0:
            return None

        if current_subtotal < (fee.free_after_subtotal or 0):
            return ProgressBar(
                image=self._bonus_settings.progress_bar_image_info,
                current_value=current_subtotal,
                placeholders=[],
                items=[
                    ProgressBarItem(
                        title=self._bonus_settings.small_order_fee_no_bonus.first_bar_title.format(
                            remaining_amount=((fee.free_after_subtotal or 0) - current_subtotal) / 100,
                        ),
                        total_value=fee.free_after_subtotal,
                        subtitle=self._bonus_settings.small_order_fee_no_bonus.first_bar_subtitle,
                        type=ProgressBarItemType.fee,
                    )
                ],
            )

        return ProgressBar(
            image=self._bonus_settings.progress_bar_image_info,
            current_value=current_subtotal,
            placeholders=[
                PlaceholderItem(title=title)
                for title in self._bonus_settings.small_order_fee_no_bonus_passed.placeholders_split
            ],
            items=[],
        )

    def get_fee_cart_bar(self, fee: Fee, current_subtotal: int) -> Optional[ProgressBar]:
        if fee.value == 0:
            return None

        if current_subtotal == 0:
            return None

        if current_subtotal < (fee.free_after_subtotal or 0):
            if current_subtotal < (fee.free_after_subtotal or 0):
                return ProgressBar(
                    image=self._bonus_settings.progress_bar_image_info,
                    current_value=current_subtotal,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_fee_no_bonus.first_bar_title.format(
                                remaining_amount=((fee.free_after_subtotal or 0) - current_subtotal) / 100,
                            ),
                            total_value=fee.free_after_subtotal,
                            subtitle=self._bonus_settings.small_order_fee_no_bonus.first_bar_subtitle,
                            type=ProgressBarItemType.fee,
                        )
                    ],
                )

        return None
