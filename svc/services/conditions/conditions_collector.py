import abc
from abc import abstractmethod
from dataclasses import dataclass
from logging import getLogger
from typing import List, Optional, Tuple, Union

from svc.api.models.conditions import (
    ConditionsOrderItem,
    OrderConditions,
    OrderConditionsItem,
    ProgressBar,
    ProgressBarItem,
    ProgressBarItemType,
)
from svc.persist.dao.fee import Fee
from svc.services.conditions.bonus_manager import OrderBonus
from svc.services.gift.dto import GiftPromotionSettingsModel
from svc.services.gift.gift_manager import GiftManager
from svc.settings import Settings, get_service_settings

logger = getLogger(__name__)


@dataclass
class ProgressBarValue:
    value: Optional[int]
    completed: bool


def title_chain(progress_bar_items: list[ProgressBarItem], progress_bar_values: list[ProgressBarValue]) -> None:
    title = ""
    for pb_item, pb_value in zip(progress_bar_items, progress_bar_values):
        if pb_value.completed is False:
            break

        if not title:
            if len(progress_bar_items) == 3:
                title = f"{pb_item.title}"
            else:
                title = f"Yay, {pb_item.title}"
        else:
            title = f"{title} + {pb_item.title}"
        pb_item.title = title


class BaseChain(abc.ABC):
    """
    Interface for chains to calculate order conditions and promotions effects
    """

    @abstractmethod
    def get_progress_bar_value(self) -> ProgressBarValue:
        pass

    @abstractmethod
    def get_progress_bar_item(self) -> Optional[ProgressBarItem]:
        pass

    @abstractmethod
    async def get_condition_item(self) -> Optional[ConditionsOrderItem]:
        pass


class FeeChain(BaseChain):
    def __init__(
        self,
        fee: Fee,
        fee_subtotal: int,
        settings: Settings = get_service_settings(),
    ):
        self.fee = fee
        self.fee_subtotal = fee_subtotal
        self.bonus_settings = settings.order_bonus_settings
        self.conditions_settings = settings.order_conditions_settings

    def get_progress_bar_value(self) -> ProgressBarValue:
        if self.fee_subtotal < (self.fee.free_after_subtotal or 0):
            return ProgressBarValue(value=self.fee_subtotal, completed=False)
        return ProgressBarValue(value=self.fee.free_after_subtotal, completed=True)

    def _choose_progress_bar_item_title(self) -> str:
        if self.fee and self.fee_subtotal < (self.fee.free_after_subtotal or 0):
            return "Add ${remaining_amount:4.2f} to get free delivery".format(
                remaining_amount=((self.fee.free_after_subtotal or 0) - self.fee_subtotal) / 100
            )

        return "Free delivery"

    def get_progress_bar_item(self) -> Optional[ProgressBarItem]:
        title = self._choose_progress_bar_item_title()
        total_value = (self.fee.free_after_subtotal or 0) if self.fee else 0

        return ProgressBarItem(title=title, total_value=total_value, type=ProgressBarItemType.fee)

    async def get_condition_item(self) -> Optional[OrderConditionsItem]:

        return OrderConditionsItem(
            title=self.conditions_settings.conditions_small_order_fee_title.format(
                required_amount=(self.fee.free_after_subtotal or 0) / 100,
            ),
            subtitle=self.conditions_settings.conditions_small_order_fee_subtitle.format(
                fee_amount=self.fee.fee_amount / 100,
            ),
            image=self.conditions_settings.conditions_delivery_image,
            color=None,
        )


class BonusChain(BaseChain):
    def __init__(
        self,
        left_border_value: int,
        bonus: OrderBonus,
        fee_subtotal: int,
        bonus_subtotal: int,
        settings: Settings = get_service_settings(),
    ):
        self.left_border_value = left_border_value
        self.bonus = bonus
        self.fee_subtotal = fee_subtotal
        self.bonus_subtotal = bonus_subtotal
        self.bonus_settings = settings.order_bonus_settings
        self.conditions_settings = settings.order_conditions_settings

    def get_progress_bar_value(self) -> ProgressBarValue:
        if self.bonus_subtotal < self.left_border_value:
            return ProgressBarValue(value=None, completed=False)
        if self.left_border_value <= self.bonus_subtotal < self.bonus.required_subtotal:
            if self.fee_subtotal != self.bonus_subtotal:
                bonus_k = self.bonus_subtotal / self.bonus.required_subtotal
                return ProgressBarValue(
                    value=int(
                        self.left_border_value + (self.bonus.required_subtotal - self.left_border_value) * bonus_k
                    ),
                    completed=False,
                )
            else:
                return ProgressBarValue(value=self.bonus_subtotal, completed=False)

        return ProgressBarValue(value=self.bonus.required_subtotal, completed=True)

    def _choose_progress_bar_item_title(self) -> str:
        if self.bonus_subtotal < self.bonus.required_subtotal:
            return "Add ${remaining_amount:4.2f} to get {bonus_amount} off".format(
                remaining_amount=(self.bonus.required_subtotal - self.bonus_subtotal) / 100,
                bonus_amount=self.bonus.bonus_pretty,
            )
        return f"{self.bonus.bonus_pretty} off"

    def get_progress_bar_item(self) -> Optional[ProgressBarItem]:
        title = self._choose_progress_bar_item_title()

        return ProgressBarItem(title=title, total_value=self.bonus.required_subtotal, type=ProgressBarItemType.bonus)

    async def get_condition_item(self) -> OrderConditionsItem:
        return OrderConditionsItem(
            title=self.conditions_settings.conditions_bonus_title.format(
                bonus_amount=self.bonus.bonus_pretty,
                required_amount=self.bonus.required_subtotal / 100,
            ),
            subtitle=self.conditions_settings.conditions_bonus_subtitle,
            image=self.conditions_settings.conditions_bonus_image,
            color=None,
        )


class GiftChain(BaseChain):
    def __init__(
        self,
        left_border_value: int,
        gift: GiftPromotionSettingsModel,
        fee_subtotal: int,
        bonus_subtotal: int,
        gift_manager: GiftManager,
        settings: Settings = get_service_settings(),
    ):
        self.left_border_value = left_border_value
        self.gift = gift
        self.fee_subtotal = fee_subtotal
        self.bonus_subtotal = bonus_subtotal
        self._gift_manager = gift_manager
        self.bonus_settings = settings.order_bonus_settings
        self.conditions_settings = settings.order_conditions_settings

    def get_progress_bar_value(self) -> ProgressBarValue:
        if self.fee_subtotal < self.left_border_value:
            return ProgressBarValue(value=None, completed=False)

        if self.left_border_value <= self.fee_subtotal < self.gift.min_sum:
            return ProgressBarValue(value=self.fee_subtotal, completed=False)

        return ProgressBarValue(value=self.gift.min_sum, completed=True)

    def _choose_progress_bar_item_title(self) -> str:
        if self.bonus_subtotal < self.gift.min_sum:
            return "${remaining_amount:4.2f} to get a Gift".format(
                remaining_amount=(self.gift.min_sum - self.bonus_subtotal) / 100
            )
        return "Gift!"

    def get_progress_bar_item(self) -> Optional[ProgressBarItem]:
        title = self._choose_progress_bar_item_title()

        return ProgressBarItem(title=title, total_value=self.gift.min_sum, type=ProgressBarItemType.gift)

    async def get_condition_item(self) -> Optional[OrderConditionsItem]:
        min_sum = self.gift.min_sum
        if self.bonus_subtotal < min_sum:
            banner_id = self.gift.less_sum_banner_id
        else:
            banner_id = self.gift.greater_sum_banner_id

        if banner_id:
            banner = await self._gift_manager.get_banner(banner_id)
        else:
            banner = None

        return OrderConditionsItem(
            title=banner.title if banner else None,
            subtitle=banner.description if banner else None,
            image=banner.image_url if banner else None,
            color=None,
        )


class Composer:
    def __init__(
        self,
        bonus_subtotal: int,
        fee_subtotal: int,
        fee: Optional[Fee],
        bonus: Optional[OrderBonus],
        gift: Optional[GiftPromotionSettingsModel],
        user_orders_count: int,
        gift_manager: GiftManager,
        settings: Settings = get_service_settings(),
    ):
        self.bonus_subtotal = bonus_subtotal
        self.fee_subtotal = fee_subtotal
        self.fee = fee
        self.bonus = bonus
        self.gift = gift
        self.gift_manager = gift_manager
        self.user_orders_count = user_orders_count
        self.bonus_settings = settings.order_bonus_settings
        self.conditions_settings = settings.order_conditions_settings

    def init_chains(self) -> List[Union[FeeChain, BonusChain, GiftChain]]:
        chains = []
        if self.fee and self.user_orders_count >= self.bonus_settings.max_free_small_orders:
            chains.append(FeeChain(fee=self.fee, fee_subtotal=self.fee_subtotal))

        if self.bonus and self.gift:
            prev_border_value = chains[-1].get_progress_bar_value() if chains else None
            if prev_border_value:
                left_border_value = prev_border_value.value if prev_border_value.value else 0
            else:
                left_border_value = 0
            if self.bonus.required_subtotal < self.gift.min_sum:
                chains.append(
                    BonusChain(
                        left_border_value=left_border_value,
                        bonus=self.bonus,
                        fee_subtotal=self.fee_subtotal,
                        bonus_subtotal=self.bonus_subtotal,
                    )
                )
                prev_border_value = chains[-1].get_progress_bar_value() if chains else None
                if prev_border_value:
                    left_border_value = prev_border_value.value if prev_border_value.value else 0
                else:
                    left_border_value = 0
                chains.append(
                    GiftChain(
                        left_border_value=left_border_value,
                        gift=self.gift,
                        fee_subtotal=self.fee_subtotal,
                        bonus_subtotal=self.bonus_subtotal,
                        gift_manager=self.gift_manager,
                    )
                )
            else:
                chains.append(
                    GiftChain(
                        left_border_value=left_border_value,
                        gift=self.gift,
                        fee_subtotal=self.fee_subtotal,
                        bonus_subtotal=self.bonus_subtotal,
                        gift_manager=self.gift_manager,
                    )
                )
                prev_border_value = chains[-1].get_progress_bar_value() if chains else None
                if prev_border_value:
                    left_border_value = prev_border_value.value if prev_border_value.value else 0
                else:
                    left_border_value = 0
                BonusChain(
                    left_border_value=left_border_value,
                    bonus=self.bonus,
                    fee_subtotal=self.fee_subtotal,
                    bonus_subtotal=self.bonus_subtotal,
                )
            return chains

        if self.gift:
            prev_border_value = chains[-1].get_progress_bar_value() if chains else None
            if prev_border_value:
                left_border_value = prev_border_value.value if prev_border_value.value else 0
            else:
                left_border_value = 0
            chains.append(
                GiftChain(
                    left_border_value=left_border_value,
                    gift=self.gift,
                    fee_subtotal=self.fee_subtotal,
                    bonus_subtotal=self.bonus_subtotal,
                    gift_manager=self.gift_manager,
                )
            )
            return chains

        if self.bonus:
            prev_border_value = chains[-1].get_progress_bar_value() if chains else None
            if prev_border_value:
                left_border_value = prev_border_value.value if prev_border_value.value else 0
            else:
                left_border_value = 0
            chains.append(
                BonusChain(
                    left_border_value=left_border_value,
                    bonus=self.bonus,
                    fee_subtotal=self.fee_subtotal,
                    bonus_subtotal=self.bonus_subtotal,
                )
            )
        return chains

    async def compose(self) -> Tuple[Optional[ProgressBar], Optional[ProgressBar], Optional[OrderConditions]]:
        active_chains = self.init_chains()
        if not active_chains:
            return None, None, None

        progress_bar_values = [it.get_progress_bar_value() for it in active_chains]
        progress_bar_items = [it.get_progress_bar_item() for it in active_chains]
        order_conditions_items = [await it.get_condition_item() for it in active_chains]

        order_conditions = OrderConditions(
            image=self.conditions_settings.order_conditions_image,
            items=[it for it in order_conditions_items if it is not None],
        )
        progress_bar_items = [it for it in progress_bar_items if it is not None]
        pb_values = [it for it in progress_bar_values if it.value is not None]
        title_chain(progress_bar_items, pb_values)

        progress_bar = ProgressBar(
            current_value=next(it.value for it in reversed(progress_bar_values) if it.value is not None),
            items=progress_bar_items,
        )

        return progress_bar, progress_bar, order_conditions
