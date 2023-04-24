import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple
from uuid import UUID

from pydantic import PositiveInt

from svc.api.models.coupon import DistributedDiscountItemShort
from svc.api.models.order import OrderItem, ProductType

logger = logging.getLogger(__name__)


@dataclass
class DistributedDiscountItem:
    order_item_id: UUID
    rounded_coupon_discount: int
    initial_coupon_discount: Decimal
    item_actual_price: int
    max_discount: PositiveInt | None


@dataclass
class CalculatedDistributedDiscount:
    value: int
    items: List[DistributedDiscountItemShort]


def calculate_order_distributed_discount(
    discount_value: int,
    order_items: Iterable[OrderItem],
    purchase_prices_mapper: Dict[UUID, int],
) -> CalculatedDistributedDiscount:
    distributed_items = _largest_remainder_method_round(order_items, discount_value, purchase_prices_mapper)
    result_items = []
    for item in order_items:
        result_items.append(
            DistributedDiscountItemShort(order_item_id=item.id, distributed_discount=distributed_items.get(item.id, 0))
        )
    return CalculatedDistributedDiscount(
        value=sum(it.distributed_discount for it in result_items),
        items=result_items,
    )


def _largest_remainder_method_round(
    order_items: Iterable[OrderItem],
    order_discount: int,
    purchase_prices_mapper: Dict[UUID, int],
) -> Dict[UUID, int]:
    order_subtotal = sum(item.actual_price * item.quantity for item in order_items)
    if not order_subtotal:
        return {}
    coupon_discount_factor = Decimal(order_discount) / order_subtotal
    coupon_items = (
        _create_coupon_item(coupon_discount_factor, order_item, purchase_prices_mapper) for order_item in order_items
    )
    rounded = sorted(coupon_items, key=_remainder_sorting_key, reverse=True)
    remained_cents = order_discount - sum(item.rounded_coupon_discount for item in rounded)
    for coupon_item in rounded:
        if remained_cents == 0:
            break

        coupon_item.rounded_coupon_discount += 1
        remained_cents -= 1

    return {
        item.order_item_id: item.rounded_coupon_discount
        if item.max_discount is None
        else min(item.rounded_coupon_discount, item.max_discount)
        for item in rounded
    }


def _remainder_sorting_key(item: DistributedDiscountItem) -> Tuple[Decimal, int]:
    return item.initial_coupon_discount - item.rounded_coupon_discount, item.item_actual_price


def _create_coupon_item(
    coupon_discount_factor: Decimal, order_item: OrderItem, purchase_prices_mapper: Dict[UUID, int]
) -> DistributedDiscountItem:
    coupon_discount = coupon_discount_factor * order_item.actual_price * order_item.quantity

    if order_item.product_type == ProductType.alcohol:
        max_discount = int(
            min(
                order_item.actual_price - purchase_prices_mapper.get(order_item.product_id, 0),
                order_item.actual_price * 0.35,
            )
        )
        if max_discount < 0:
            logger.warning(
                f"[product_id={order_item.product_id}, actual_price={order_item.actual_price}, "
                f"purchase_price={purchase_prices_mapper[order_item.product_id]}] "
                f"Purchase_price of the product is bigger than actual_price."
            )

        max_discount = PositiveInt(max_discount * order_item.quantity)

    else:
        max_discount = None

    return DistributedDiscountItem(
        order_item_id=order_item.id,
        rounded_coupon_discount=int(coupon_discount),
        initial_coupon_discount=coupon_discount,
        item_actual_price=order_item.actual_price * order_item.quantity,
        max_discount=max_discount,
    )
