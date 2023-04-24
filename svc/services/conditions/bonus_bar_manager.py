from fastapi import Depends

from svc.api.models.conditions import PlaceholderItem, ProgressBar, ProgressBarItem, ProgressBarItemType
from svc.persist.dao.fee import Fee
from svc.services.conditions.bonus_manager import OrderBonus
from svc.settings import Settings, get_service_settings


class BonusProgressBarManager:
    def __init__(self, settings: Settings = Depends(get_service_settings)):
        self._bonus_settings = settings.order_bonus_settings

    def get_fee_catalog_bar(
        self,
        fee: Fee,
        bonus: OrderBonus,
        fee_subtotal: int,
        bonus_subtotal: int,
        user_orders_count: int,
    ) -> ProgressBar:
        if user_orders_count < self._bonus_settings.max_free_small_orders:
            if bonus_subtotal == 0:
                return ProgressBar(
                    current_value=bonus_subtotal,
                    image=self._bonus_settings.progress_bar_image_bonus,
                    placeholders=[
                        PlaceholderItem(
                            title=title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            )
                        )
                        for title in self._bonus_settings.small_order_with_bonus_empty.placeholders_split
                    ],
                    items=[],
                )
            elif bonus_subtotal < bonus.required_subtotal:
                return ProgressBar(
                    current_value=bonus_subtotal,
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_second_title.second_bar_title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            ),
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                            total_value=bonus.required_subtotal,
                            type=ProgressBarItemType.bonus,
                        )
                    ],
                )
            else:
                return ProgressBar(
                    current_value=bonus_subtotal,
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[
                        PlaceholderItem(title=title.format(bonus_amount=bonus.bonus_pretty))
                        for title in self._bonus_settings.small_order_with_bonus_on.placeholders_split
                    ],
                    items=[],
                )
        else:
            free_after_subtotal = fee.free_after_subtotal or 0
            if fee_subtotal == 0:
                return ProgressBar(
                    current_value=fee_subtotal,
                    image=self._bonus_settings.progress_bar_image_bonus,
                    placeholders=[
                        PlaceholderItem(
                            title=title.format(
                                remaining_amount=(bonus.required_subtotal - fee_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            )
                        )
                        for title in self._bonus_settings.small_order_with_bonus_empty.placeholders_split
                    ],
                    items=[],
                )
            elif fee_subtotal < free_after_subtotal:
                return ProgressBar(
                    current_value=fee_subtotal,
                    image=self._bonus_settings.progress_bar_image_bonus,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_first_title.first_bar_title.format(
                                remaining_amount=(free_after_subtotal - fee_subtotal) / 100,
                            ),
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.first_bar_subtitle,
                            total_value=free_after_subtotal,
                            type=ProgressBarItemType.fee,
                        ),
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_first_title.second_bar_title,
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                            total_value=bonus.required_subtotal,
                            type=ProgressBarItemType.bonus,
                        ),
                    ],
                )
            elif bonus_subtotal < bonus.required_subtotal:
                if fee_subtotal != bonus_subtotal:
                    bonus_k = bonus_subtotal / bonus.required_subtotal
                    current_value = free_after_subtotal + (bonus.required_subtotal - free_after_subtotal) * bonus_k
                else:
                    current_value = bonus_subtotal
                return ProgressBar(
                    current_value=current_value,
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_double_title.first_bar_title,
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.first_bar_subtitle,
                            total_value=free_after_subtotal,
                            type=ProgressBarItemType.fee,
                        ),
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_double_title.second_bar_title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            ),
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                            total_value=bonus.required_subtotal,
                            type=ProgressBarItemType.bonus,
                        ),
                    ],
                )
            else:
                return ProgressBar(
                    current_value=max(fee_subtotal, bonus_subtotal),
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[
                        PlaceholderItem(title=title.format(bonus_amount=bonus.bonus_pretty))
                        for title in self._bonus_settings.small_order_with_bonus_on.placeholders_split
                    ],
                    items=[],
                )

    def get_fee_cart_bar(
        self,
        fee: Fee,
        bonus: OrderBonus,
        fee_subtotal: int,
        bonus_subtotal: int,
        user_orders_count: int,
    ) -> ProgressBar:
        if user_orders_count < self._bonus_settings.max_free_small_orders:
            if bonus_subtotal == 0:
                return ProgressBar(
                    current_value=bonus_subtotal,
                    image=self._bonus_settings.progress_bar_image_bonus,
                    placeholders=[
                        PlaceholderItem(
                            title=title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            )
                        )
                        for title in self._bonus_settings.small_order_with_bonus_empty.placeholders_split
                    ],
                    items=[],
                )
            elif bonus_subtotal < bonus.required_subtotal:
                return ProgressBar(
                    current_value=bonus_subtotal,
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_second_title.second_bar_title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            ),
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                            total_value=bonus.required_subtotal,
                            type=ProgressBarItemType.bonus,
                        )
                    ],
                )
            else:
                return ProgressBar(
                    current_value=bonus_subtotal,
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[
                        PlaceholderItem(title=title.format(bonus_amount=bonus.bonus_pretty))
                        for title in self._bonus_settings.small_order_with_bonus_on.placeholders_split
                    ],
                    items=[],
                )
        else:
            free_after_subtotal = fee.free_after_subtotal or 0
            if fee_subtotal == 0:
                return ProgressBar(
                    current_value=fee_subtotal,
                    image=self._bonus_settings.progress_bar_image_bonus,
                    placeholders=[
                        PlaceholderItem(
                            title=title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            )
                        )
                        for title in self._bonus_settings.small_order_with_bonus_empty.placeholders_split
                    ],
                    items=[],
                )
            elif fee_subtotal < free_after_subtotal:
                return ProgressBar(
                    current_value=fee_subtotal,
                    image=self._bonus_settings.progress_bar_image_bonus,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_first_title.first_bar_title.format(
                                remaining_amount=(free_after_subtotal - fee_subtotal) / 100,
                            ),
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.first_bar_subtitle,
                            total_value=free_after_subtotal,
                            type=ProgressBarItemType.fee,
                        ),
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_first_title.second_bar_title,
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                            total_value=bonus.required_subtotal,
                            type=ProgressBarItemType.bonus,
                        ),
                    ],
                )
            elif bonus_subtotal < bonus.required_subtotal:
                if fee_subtotal != bonus_subtotal:
                    bonus_k = bonus_subtotal / bonus.required_subtotal
                    current_value = free_after_subtotal + (bonus.required_subtotal - free_after_subtotal) * bonus_k
                else:
                    current_value = bonus_subtotal
                return ProgressBar(
                    current_value=current_value,
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[],
                    items=[
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_second_title.first_bar_title,
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.first_bar_subtitle,
                            total_value=free_after_subtotal,
                            type=ProgressBarItemType.fee,
                        ),
                        ProgressBarItem(
                            title=self._bonus_settings.small_order_with_bonus_second_title.second_bar_title.format(
                                remaining_amount=(bonus.required_subtotal - bonus_subtotal) / 100,
                                bonus_amount=bonus.bonus_pretty,
                            ),
                            subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                            total_value=bonus.required_subtotal,
                            type=ProgressBarItemType.bonus,
                        ),
                    ],
                )
            else:
                return ProgressBar(
                    current_value=max(fee_subtotal, bonus_subtotal),
                    image=self._bonus_settings.progress_bar_image_info,
                    placeholders=[
                        PlaceholderItem(title=title.format(bonus_amount=bonus.bonus_pretty))
                        for title in self._bonus_settings.small_order_with_bonus_on.placeholders_split
                    ],
                    items=[],
                )

    def get_bonus_cart_bar(self, bonus: OrderBonus, current_subtotal: int) -> ProgressBar:
        if current_subtotal == 0:
            return ProgressBar(
                current_value=current_subtotal,
                image=self._bonus_settings.progress_bar_image_bonus,
                placeholders=[
                    PlaceholderItem(
                        title=title.format(
                            remaining_amount=bonus.required_subtotal / 100,
                            bonus_amount=bonus.bonus_pretty,
                        ),
                    )
                    for title in self._bonus_settings.small_order_with_bonus_empty.placeholders_split
                ],
                items=[],
            )
        elif current_subtotal < bonus.required_subtotal:
            return ProgressBar(
                current_value=current_subtotal,
                image=self._bonus_settings.progress_bar_image_info,
                placeholders=[],
                items=[
                    ProgressBarItem(
                        title=self._bonus_settings.small_order_with_bonus_second_title.second_bar_title.format(
                            remaining_amount=(bonus.required_subtotal - current_subtotal) / 100,
                            bonus_amount=bonus.bonus_pretty,
                        ),
                        subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                        total_value=bonus.required_subtotal,
                        type=ProgressBarItemType.bonus,
                    )
                ],
            )
        else:
            return ProgressBar(
                current_value=current_subtotal,
                image=self._bonus_settings.progress_bar_image_info,
                placeholders=[
                    PlaceholderItem(title=title.format(bonus_amount=bonus.bonus_pretty))
                    for title in self._bonus_settings.small_order_with_bonus_on.placeholders_split
                ],
                items=[],
            )

    def get_bonus_catalog_bar(self, bonus: OrderBonus, current_subtotal: int) -> ProgressBar:
        if current_subtotal == 0:
            return ProgressBar(
                current_value=current_subtotal,
                image=self._bonus_settings.progress_bar_image_bonus,
                placeholders=[
                    PlaceholderItem(
                        title=title.format(
                            remaining_amount=((bonus.required_subtotal or 0) - current_subtotal) / 100,
                            bonus_amount=bonus.bonus_pretty,
                        )
                    )
                    for title in self._bonus_settings.small_order_with_bonus_empty.placeholders_split
                ],
                items=[],
            )
        elif current_subtotal < bonus.required_subtotal:
            return ProgressBar(
                current_value=current_subtotal,
                image=self._bonus_settings.progress_bar_image_info,
                placeholders=[],
                items=[
                    ProgressBarItem(
                        title=self._bonus_settings.small_order_with_bonus_second_title.second_bar_title.format(
                            remaining_amount=(bonus.required_subtotal - current_subtotal) / 100,
                            bonus_amount=bonus.bonus_pretty,
                        ),
                        subtitle=self._bonus_settings.small_order_with_bonus_first_title.second_bar_subtitle,
                        total_value=bonus.required_subtotal,
                        type=ProgressBarItemType.bonus,
                    )
                ],
            )
        else:
            return ProgressBar(
                current_value=current_subtotal,
                image=self._bonus_settings.progress_bar_image_info,
                placeholders=[
                    PlaceholderItem(title=title.format(bonus_amount=bonus.bonus_pretty))
                    for title in self._bonus_settings.small_order_with_bonus_on.placeholders_split
                ],
                items=[],
            )
