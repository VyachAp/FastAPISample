from logging import getLogger
from typing import Optional

from fastapi import Depends

from svc.api.models.conditions import (
    Bonus,
    DeliveryPromise,
    FeeModel,
    GetOrderConditionsRequest,
    OrderConditionsResponse,
)
from svc.api.models.order import ProductType
from svc.infrastructure.pricing.pricing_manager import PricingManager
from svc.persist.dao.fee import Fee
from svc.persist.schemas.fee import FeeType
from svc.services.adapters.warehouse_adapter import WarehouseAdapter
from svc.services.conditions.bar_manager import BarManager
from svc.services.conditions.bonus_manager import OrderBonusManager
from svc.services.conditions.conditions_collector import Composer
from svc.services.conditions.conditions_manager import ConditionsManager
from svc.services.conditions.fee_manager import FeeManager
from svc.services.gift.gift_manager import GiftManager

logger = getLogger(__name__)


class OrderConditionsService:
    def __init__(
        self,
        fee_manager: FeeManager = Depends(FeeManager),
        bonus_manager: OrderBonusManager = Depends(OrderBonusManager),
        progress_bar_manager: BarManager = Depends(BarManager),
        order_conditions_manager: ConditionsManager = Depends(ConditionsManager),
        warehouse_adapter: WarehouseAdapter = Depends(WarehouseAdapter),
        pricing_manager: PricingManager = Depends(PricingManager),
        gift_manager: GiftManager = Depends(GiftManager),
    ):
        self._fee_manager = fee_manager
        self._bonus_manager = bonus_manager
        self._progress_bar_manager = progress_bar_manager
        self._conditions_manager = order_conditions_manager
        self._warehouse_adapter = warehouse_adapter
        self._pricing_manager = pricing_manager
        self._gift_manager = gift_manager

    async def get_order_conditions(self, request: GetOrderConditionsRequest) -> OrderConditionsResponse:
        logger.debug(f"Received conditions request: {request}")

        bonus_applicable_order_items = [it for it in request.order_items if it.product_type != ProductType.tobacco]
        bonus_calculation_subtotal = sum(it.actual_price * it.quantity for it in bonus_applicable_order_items)
        fee_calculation_subtotal = sum(it.actual_price * it.quantity for it in request.order_items)

        fees = await self._fee_manager.calculate_fees(
            user_id=request.user_id,
            warehouse_id=request.warehouse_id,
            user_orders_count=request.user_order_count,
            order_subtotal=fee_calculation_subtotal,
        )

        if request.coupon_applied:
            bonus = None
        else:
            warehouse = await self._warehouse_adapter.get_warehouse(request.warehouse_id)
            purchase_prices_mapper = await self._pricing_manager.get_product_prices_mapper(
                warehouse_id=request.warehouse_id,
                product_ids=[
                    it.product_id for it in bonus_applicable_order_items if it.product_type == ProductType.alcohol
                ],
            )
            bonus = await self._bonus_manager.calculate_order_bonus(
                warehouse=warehouse,
                order_subtotal=bonus_calculation_subtotal,
                delivery_mode=request.delivery_mode,
                order_items=bonus_applicable_order_items,
                purchase_prices_mapper=purchase_prices_mapper,
            )

        gift = await self._gift_manager.get_active_gift_promotion_settings(request.warehouse_id)

        delivery_promise = DeliveryPromise(
            delivery_mode=request.delivery_mode,
            text=None,
        )

        fee_models = [
            FeeModel(
                id=fee.id,
                name=fee.name,
                description=fee.description,
                value=fee.value,
                image=fee.image,
                fee_type=fee.fee_type,
            )
            for fee in fees
        ]

        small_order_fee: Optional[Fee] = next((fee for fee in fees if fee.fee_type == FeeType.small_order), None)
        if request.legacy_mode:
            # Logic for old version
            return OrderConditionsResponse(
                fees=fee_models,
                bonus=Bonus(value=bonus.applied_bonus if bonus else 0),
                delivery_promise=delivery_promise,
                catalog_progress_bar=self._progress_bar_manager.get_catalog_bar(
                    fee=small_order_fee,
                    bonus=bonus,
                    fee_subtotal=fee_calculation_subtotal,
                    bonus_subtotal=bonus_calculation_subtotal,
                    user_orders_count=request.user_order_count,
                ),
                cart_progress_bar=self._progress_bar_manager.get_cart_bar(
                    fee=small_order_fee,
                    bonus=bonus,
                    fee_subtotal=fee_calculation_subtotal,
                    bonus_subtotal=bonus_calculation_subtotal,
                    user_orders_count=request.user_order_count,
                ),
                order_conditions=self._conditions_manager.get_order_conditions(
                    fee=small_order_fee,
                    bonus=bonus,
                    user_orders_count=request.user_order_count,
                ),
                distributed_discount_items=bonus.discounted_items if bonus is not None else [],
            )

        catalog_progress_bar, cart_progress_bar, order_conditions = await Composer(
            bonus_subtotal=bonus_calculation_subtotal,
            fee_subtotal=fee_calculation_subtotal,
            fee=small_order_fee,
            bonus=bonus,
            gift=gift,
            user_orders_count=request.user_order_count,
            gift_manager=self._gift_manager,
        ).compose()
        result = OrderConditionsResponse(
            fees=fee_models,
            bonus=Bonus(value=bonus.applied_bonus if bonus else 0),
            delivery_promise=delivery_promise,
            catalog_progress_bar=catalog_progress_bar,
            cart_progress_bar=cart_progress_bar,
            order_conditions=order_conditions,
            distributed_discount_items=bonus.discounted_items if bonus is not None else [],
        )

        logger.debug(f"Calculated order conditions with {small_order_fee=}, {bonus=}, {result=}")

        return result
