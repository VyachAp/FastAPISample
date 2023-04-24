import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends

from svc.api.errors.coupon import (
    CouponMinAmountError,
    CouponNotFoundError,
    CouponNotPermittedCategoryError,
    CouponNotPermittedUserError,
    CouponNotPermittedWarehouseError,
    CouponNotValidError,
    CouponRedeemedError,
    CouponRedeemedLimitError,
    CouponRedeemedOrdersFromError,
    CouponRedeemedOrdersToError,
    ReferralCouponLimitError,
    ReferralCouponSelfUsageError,
)
from svc.api.errors.user import UserNotEligibleToUseCoupon
from svc.api.models.coupon import (
    AddOrderCouponRequest,
    CouponDetail,
    CreateReferralCouponRequest,
    OrderCouponDetail,
    RecalculateOrderCouponRequest,
)
from svc.api.models.order import ProductType
from svc.infrastructure.pricing.pricing_manager import PricingManager
from svc.services.antifraud.antifraud_manager import AntifraudManager
from svc.services.coupon.coupon_manager import CouponManager
from svc.services.coupon.dto import CouponType
from svc.services.gift.gift_manager import GiftManager
from svc.services.infrastructure.metrics_registry import MetricsRegistry, get_metrics_registry
from svc.services.uow import UnitOfWork
from svc.settings import Settings, get_service_settings
from svc.utils.discounting import calculate_order_distributed_discount
from svc.utils.money import cents_to_dollars

logger = logging.getLogger(__name__)


class CouponService:
    def __init__(
        self,
        coupon_manager: CouponManager = Depends(CouponManager),
        gift_manager: GiftManager = Depends(GiftManager),
        antifraud_manager: AntifraudManager = Depends(AntifraudManager),
        pricing_manager: PricingManager = Depends(PricingManager),
        config: Settings = Depends(get_service_settings),
        uow: UnitOfWork = Depends(UnitOfWork),
        metrics_registry: MetricsRegistry = Depends(get_metrics_registry),
    ) -> None:
        self._coupon_manager = coupon_manager
        self._gift_manager = gift_manager
        self._antifraud_manager = antifraud_manager
        self._pricing_manager = pricing_manager
        self._config = config
        self._uow = uow
        self._metrics_registry = metrics_registry

    async def get_coupon(self, coupon_id: UUID) -> Optional[CouponDetail]:
        coupon = await self._coupon_manager.get_coupon(coupon_id)
        if coupon is None:
            raise CouponNotFoundError()

        return CouponDetail(
            id=coupon.id,
            name=coupon.name,
            kind=coupon.kind,
            value=coupon.value,
            min_order_amount=coupon.minimum_order_amount,
        )

    async def antifraud_check(self, user_id: UUID, unique_identifier: Optional[str]) -> None:
        # In case of QA
        if unique_identifier and self._config.user_antifraud.check_enabled:
            is_user_whitelisted = await self._antifraud_manager.is_user_whitelisted(user_id=user_id)
            if is_user_whitelisted:
                self._metrics_registry.register_whitelisted_user_antifraud_coupon_usage(user_id, unique_identifier)

            is_identifier_ignored = await self._antifraud_manager.is_identifier_whitelisted(
                identifier=unique_identifier
            )
            if is_identifier_ignored:
                self._metrics_registry.register_whitelisted_fingerprint_antifraud_coupon_usage(
                    user_id, unique_identifier
                )

            if not (is_user_whitelisted or is_identifier_ignored):
                amount_of_users_per_fingerprint = await self._antifraud_manager.get_amount_of_users_by_identifier(
                    unique_identifier, user_id
                )
                if amount_of_users_per_fingerprint >= self._config.user_antifraud.amount_of_users_per_fingerprint:
                    logger.info(
                        f"[user_id={user_id}] User counted as a fraud. "
                        f"Fingerprint has used for {amount_of_users_per_fingerprint} more users",
                    )
                    self._metrics_registry.register_antifraud_coupon_ban(user_id, unique_identifier)
                    raise UserNotEligibleToUseCoupon()

    async def add_coupon(self, order_id: UUID, coupon_request: AddOrderCouponRequest) -> OrderCouponDetail:
        user_id = coupon_request.user_id
        warehouse_id = coupon_request.warehouse_id
        coupon_name = coupon_request.name
        paid_orders_count = coupon_request.paid_orders_count
        delivered_orders_count = coupon_request.delivered_orders_count
        unique_identifier = coupon_request.unique_identifier
        cart_message_args = None

        await self.antifraud_check(user_id=user_id, unique_identifier=unique_identifier)
        # Get coupon by name
        coupon = await self._coupon_manager.get_active_coupon_by_name(coupon_name)
        if coupon is None:
            raise CouponNotValidError()

        if coupon.coupon_type == CouponType.referral and coupon.user_id == user_id:
            raise ReferralCouponSelfUsageError()

        if not await self._coupon_manager.is_permitted_user(user_id=user_id, coupon_id=coupon.id):
            logger.info(
                f"[user_id={user_id}, coupon_id={coupon.id}] Coupon is not permitted for the user...",
            )
            raise CouponNotPermittedUserError()

        if not await self._coupon_manager.is_permitted_warehouse(warehouse_id=warehouse_id, coupon_id=coupon.id):
            logger.info(
                f"[warehouse_id={warehouse_id}, coupon_id={coupon.id}] Coupon is not permitted for the warehouse...",
            )
            raise CouponNotPermittedWarehouseError()

        permitted_categories = await self._coupon_manager.get_permitted_categories_ids(coupon.id)
        order_items = [item for item in coupon_request.order_items if item.product_type != ProductType.tobacco]

        if order_items and permitted_categories:
            order_items = self._coupon_manager.filter_items_for_permitted_categories(
                order_items=coupon_request.order_items,
                categories_ids=permitted_categories,
            )
            if not order_items:
                order_categories = {
                    category_id for item in coupon_request.order_items for category_id in item.categories_ids
                }
                logger.info(
                    f"[categories_ids=[{', '.join(str(it) for it in order_categories)}], "
                    f"coupon_id={coupon.id}] Coupon is not permitted for the these categories...",
                )
                raise CouponNotPermittedCategoryError(
                    {"permitted_categories_ids": [str(it) for it in permitted_categories]}
                )

        subtotal = sum(it.subtotal for it in order_items)

        min_amount = coupon.minimum_order_amount
        if min_amount is not None and coupon_request.order_subtotal < min_amount:
            raise CouponMinAmountError({"min_amount": cents_to_dollars(min_amount)})

        old_coupon = await self._coupon_manager.get_current_order_coupon(order_id)
        if old_coupon is not None:
            logger.info(
                f"[order_id={order_id}, old_coupon.id={old_coupon.id}] Deleting old order coupon...",
            )
            # Revert coupon usage
            await self.revert_coupon_usage(old_coupon.id, order_id)

        if coupon.limit is not None:
            usages_count = await self._coupon_manager.get_user_coupon_usage_count(user_id, coupon.id)
            if usages_count >= coupon.limit:
                raise CouponRedeemedLimitError({"limit": coupon.limit})

        if coupon.orders_from is not None and coupon.orders_from > paid_orders_count:
            raise CouponRedeemedOrdersFromError({"missing_orders_amount": coupon.orders_from - paid_orders_count})

        if coupon.orders_to is not None and coupon.orders_to <= paid_orders_count:
            if CouponType(coupon.coupon_type) == CouponType.referral:
                raise ReferralCouponLimitError({"initial_orders_count_permit": coupon.orders_to})

            logger.info(
                f"You have already made more than {coupon.orders_to} orders and can no longer apply this promo code"
            )
            raise CouponRedeemedOrdersToError({"orders_amount_upper_limit": coupon.orders_to})

        if coupon.quantity is not None and coupon.quantity == 0:
            raise CouponRedeemedError()

        await self._coupon_manager.overwrite_coupon_value(coupon, delivered_orders_count)
        # Save coupon usage
        await self.store_coupon_usage(coupon.id, user_id, order_id, False, unique_identifier)
        purchase_prices_mapper = await self._pricing_manager.get_product_prices_mapper(
            warehouse_id=warehouse_id,
            product_ids=[it.product_id for it in order_items if it.product_type == ProductType.alcohol],
        )

        base_coupon_discount = self._coupon_manager.get_coupon_discount(coupon, subtotal)

        distributed_discount = calculate_order_distributed_discount(
            discount_value=base_coupon_discount,
            order_items=order_items,
            purchase_prices_mapper=purchase_prices_mapper,
        )
        coupon_discount = distributed_discount.value

        if coupon.max_discount is not None and self._coupon_manager.is_max_discount_exceeded(coupon, coupon_discount):
            logger.info(
                f"[coupon_id={coupon.id}, coupon_discount={coupon_discount}, max_discount={coupon.max_discount}]"
                f"Coupon discount exceeds max_discount value."
            )
            distributed_discount = calculate_order_distributed_discount(
                discount_value=coupon.max_discount,
                order_items=order_items,
                purchase_prices_mapper=purchase_prices_mapper,
            )
            coupon_discount = distributed_discount.value
            cart_message_args = {"max_discount": coupon_discount}

        return OrderCouponDetail(
            id=coupon.id,
            order_id=order_id,
            name=coupon_name,
            kind=coupon.kind,
            value=coupon.value,
            discount_amount=coupon_discount,
            min_order_amount=coupon.minimum_order_amount,
            cart_message_args=cart_message_args,
            distributed_discount_items=distributed_discount.items,
        )

    async def delete_coupon(self, coupon_id: UUID, order_id: UUID) -> OrderCouponDetail:
        coupon = await self._coupon_manager.get_coupon(coupon_id)
        if coupon is None:
            raise CouponNotFoundError()

        # Revert coupon usage
        await self.revert_coupon_usage(coupon_id, order_id)

        return OrderCouponDetail(
            id=coupon_id,
            order_id=order_id,
            name=coupon.name,
            kind=coupon.kind,
            value=coupon.value,
            discount_amount=0,
            min_order_amount=coupon.minimum_order_amount,
            cart_message_args=None,
            distributed_discount_items=[],
        )

    async def create_referral_coupon(self, coupon_request: CreateReferralCouponRequest) -> str:
        user_id = coupon_request.user_id
        active_user_coupon = await self._coupon_manager.get_active_referral_coupon(user_id)
        if not active_user_coupon:
            while True:
                coupon_name = self._coupon_manager.get_coupon_name()
                is_taken = await self._coupon_manager.is_coupon_name_taken(coupon_name)
                if not is_taken:
                    break

            async with self._uow.begin():
                coupon = await self._coupon_manager.create_referral_coupon(coupon_name, user_id)

            logger.info(f"[user_id={user_id}] Created referral coupon. id={coupon.id}")
        else:
            coupon_name = active_user_coupon.name

        return coupon_name

    async def recalculate_coupon_discount(
        self,
        order_id: UUID,
        coupon_id: UUID,
        coupon_request: RecalculateOrderCouponRequest,
    ) -> OrderCouponDetail:
        logger.debug(f"[recalculate_coupon_discount] {coupon_request}")
        paid_orders_count = coupon_request.paid_orders_count
        delivered_orders_count = coupon_request.delivered_orders_count
        warehouse_id = coupon_request.warehouse_id
        cart_message_args = None

        coupon = await self._coupon_manager.get_coupon(coupon_id)
        if coupon is None:
            raise CouponNotFoundError()

        if coupon.orders_from is not None and coupon.orders_from > paid_orders_count:
            raise CouponRedeemedOrdersFromError(
                {
                    "missing_orders_amount": coupon.orders_from - paid_orders_count,
                    "coupon_name": coupon.name,
                }
            )

        if coupon.orders_to is not None and coupon.orders_to <= paid_orders_count:
            raise CouponRedeemedOrdersToError(
                {
                    "orders_amount_upper_limit": coupon.orders_to,
                    "coupon_name": coupon.name,
                }
            )

        if coupon.minimum_order_amount is not None and coupon.minimum_order_amount > coupon_request.order_subtotal:
            raise CouponMinAmountError(
                {
                    "min_amount": cents_to_dollars(coupon.minimum_order_amount),
                    "coupon_name": coupon.name,
                }
            )

        if not await self._coupon_manager.is_permitted_warehouse(warehouse_id=warehouse_id, coupon_id=coupon.id):
            logger.info(
                f"[warehouse_id={warehouse_id}, coupon_id={coupon.id}] Coupon is not permitted for the warehouse...",
            )
            raise CouponNotPermittedWarehouseError({"coupon_name": coupon.name})

        permitted_categories = await self._coupon_manager.get_permitted_categories_ids(coupon.id)
        order_items = [item for item in coupon_request.order_items if item.product_type != ProductType.tobacco]

        if order_items and permitted_categories:
            order_items = self._coupon_manager.filter_items_for_permitted_categories(
                order_items=order_items,
                categories_ids=permitted_categories,
            )
            if not order_items:
                order_categories = {
                    category_id for item in coupon_request.order_items for category_id in item.categories_ids
                }
                logger.info(
                    f"[categories_ids=[{', '.join(str(it) for it in order_categories)}], "
                    f"coupon_id={coupon.id}] Coupon is not permitted for the these categories...",
                )
                raise CouponNotPermittedCategoryError(
                    {
                        "permitted_categories_ids": [str(it) for it in permitted_categories],
                        "coupon_name": coupon.name,
                    }
                )
        subtotal = sum(it.subtotal for it in order_items)

        await self._coupon_manager.overwrite_coupon_value(coupon, delivered_orders_count)

        purchase_prices_mapper = await self._pricing_manager.get_product_prices_mapper(
            warehouse_id=warehouse_id,
            product_ids=[it.product_id for it in order_items if it.product_type == ProductType.alcohol],
        )
        base_coupon_discount = self._coupon_manager.get_coupon_discount(coupon, subtotal)

        distributed_discount = calculate_order_distributed_discount(
            discount_value=base_coupon_discount,
            order_items=order_items,
            purchase_prices_mapper=purchase_prices_mapper,
        )
        coupon_discount = distributed_discount.value

        if coupon.max_discount is not None and self._coupon_manager.is_max_discount_exceeded(coupon, coupon_discount):
            logger.info(
                f"[coupon_id={coupon.id}, coupon_discount={coupon_discount}, max_discount={coupon.max_discount}]"
                f"Coupon discount exceeds max_discount value."
            )
            distributed_discount = calculate_order_distributed_discount(
                discount_value=coupon.max_discount,
                order_items=order_items,
                purchase_prices_mapper=purchase_prices_mapper,
            )
            coupon_discount = distributed_discount.value
            cart_message_args = {"max_discount": coupon_discount}

        return OrderCouponDetail(
            id=coupon_id,
            order_id=order_id,
            name=coupon.name,
            kind=coupon.kind,
            value=coupon.value,
            discount_amount=coupon_discount,
            min_order_amount=coupon.minimum_order_amount,
            cart_message_args=cart_message_args,
            distributed_discount_items=distributed_discount.items,
        )

    async def store_coupon_usage(
        self, coupon_id: UUID, user_id: UUID, order_id: UUID, order_paid: bool, unique_identifier: Optional[str]
    ) -> None:
        async with self._uow.begin():
            await self._coupon_manager.create_user_coupon(coupon_id, user_id, order_id, order_paid)
            await self._coupon_manager.decrement_coupon_quantity(coupon_id)
            if unique_identifier:
                await self._antifraud_manager.register_fingerprint_usage(user_id, unique_identifier)

    async def revert_coupon_usage(self, coupon_id: UUID, order_id: UUID) -> None:
        async with self._uow.begin():
            await self._coupon_manager.increment_coupon_quantity(coupon_id)
            await self._coupon_manager.delete_user_coupon(coupon_id, order_id)

    async def process_paid(self, order_id: UUID) -> None:
        coupon = await self._coupon_manager.get_current_order_coupon(order_id)
        if coupon is None:
            logger.info(f"[order_id={order_id}] User coupon not found. Nothing to update")

            return None

        # Set coupon applied
        async with self._uow.begin():
            await self._coupon_manager.user_coupon_set_order_paid(coupon.id, order_id)

    async def process_cancelled(self, order_id: UUID) -> None:
        coupon = await self._coupon_manager.get_current_order_coupon(order_id)
        if coupon is None:
            logger.info(f"[order_id={order_id}] User coupon not found. Nothing to delete")

            return None

        await self.revert_coupon_usage(coupon.id, order_id)
