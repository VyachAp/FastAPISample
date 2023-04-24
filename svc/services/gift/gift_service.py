import logging
from datetime import datetime
from decimal import Decimal

from fastapi import Depends

from svc.api.errors.gift import GiftSettingsMinSumError, GiftSettingsNotFoundError
from svc.api.models.gifts import (
    BannerDetails,
    BannerInfo,
    CartBannerStyle,
    GetBannerRequest,
    GetGiftRequest,
    GiftDetails,
    GiftItem,
)
from svc.services.gift.gift_manager import GiftManager
from svc.utils.money import cents_to_dollars

logger = logging.getLogger(__name__)


class GiftService:
    def __init__(
        self,
        gift_manager: GiftManager = Depends(GiftManager),
    ) -> None:
        self._gift_manager = gift_manager

    async def get_current_gift(
        self,
        request: GetGiftRequest,
    ) -> GiftDetails:
        subtotal = request.order_subtotal
        warehouse_id = request.warehouse_id
        gift_settings = await self._gift_manager.get_active_gift_promotion_settings(warehouse_id)
        if not gift_settings:
            logger.info(
                f"There are no any gift settings for warehouse_id = `{warehouse_id}` "
                f"and datetime = `{datetime.now()}`"
            )
            raise GiftSettingsNotFoundError()

        if gift_settings.min_sum > subtotal:
            logger.info(
                f"Minimal sum of gift setting is greater then order subtotal. "
                f"Subtotal = {subtotal} cents, gift_settings_id = {gift_settings.id}"
            )
            raise GiftSettingsMinSumError()

        gift_product = await self._gift_manager.get_gift_product(gift_settings.id)

        return GiftDetails(
            gifts_chain=[
                GiftItem(
                    product_id=it.product_id,
                    quantity=it.quantity,
                )
                for it in gift_product.products_chain
            ]
            if gift_product is not None
            else [],
            gift_settings_id=gift_settings.id,
        )

    async def get_banner(
        self,
        request: GetBannerRequest,
    ) -> BannerDetails:
        subtotal = request.order_subtotal
        warehouse_id = request.warehouse_id
        gift_settings = await self._gift_manager.get_active_gift_promotion_settings(warehouse_id)
        if not gift_settings:
            return BannerDetails(banner=None)

        min_sum = gift_settings.min_sum
        if subtotal < min_sum:
            banner_id = gift_settings.less_sum_banner_id
            remaining_amount = cents_to_dollars(min_sum - subtotal)
            style_type = CartBannerStyle.info
        else:
            banner_id = gift_settings.greater_sum_banner_id
            remaining_amount = Decimal(0.0)
            style_type = CartBannerStyle.done

        if banner_id is None:
            logger.debug(f"[warehouse_id={warehouse_id}, gift_promotion_settings_id={gift_settings.id}] No *_banner_id")
            banner = None
        else:
            banner = await self._gift_manager.get_banner(banner_id)
            if banner is None:
                logger.debug(
                    f"[warehouse_id={warehouse_id}, gift_promotion_settings_id={gift_settings.id}] "
                    f"CartBanner not found"
                )

        banner_info = (
            BannerInfo(
                id=banner.id,
                img_url=banner.image_url,
                style=style_type,
                title=banner.title,
                description=banner.description,
                btn_text=banner.btn_text.format(remaining_amount) if banner.btn_text is not None else None,
            )
            if banner is not None
            else None
        )

        return BannerDetails(banner=banner_info)
