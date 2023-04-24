from uuid import uuid4

from svc.api.models.order import OrderItem, ProductType
from svc.utils.discounting import calculate_order_distributed_discount


def test_distributed_discount_should_consider_alco_products_when_purchase_price_available():
    discount_value = 400
    order_items = [
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.regular, actual_price=100, quantity=4),
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.alcohol, actual_price=100, quantity=4),
    ]
    purchase_prices_mapper = {
        order_items[-1].product_id: 90,
    }
    discount = calculate_order_distributed_discount(
        discount_value=discount_value,
        order_items=order_items,
        purchase_prices_mapper=purchase_prices_mapper,
    )
    assert discount.value == 200 + 40
    alco_discount_item = next(it for it in discount.items if it.order_item_id == order_items[-1].id)
    assert alco_discount_item.distributed_discount == 40


def test_distributed_discount_should_consider_discount_threshold_when_alco_products():
    discount_value = 400
    order_items = [
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.regular, actual_price=100, quantity=4),
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.alcohol, actual_price=100, quantity=4),
    ]
    purchase_prices_mapper = {
        order_items[-1].product_id: 50,
    }
    discount = calculate_order_distributed_discount(
        discount_value=discount_value,
        order_items=order_items,
        purchase_prices_mapper=purchase_prices_mapper,
    )
    assert discount.value == 200 + 140
    alco_discount_item = next(it for it in discount.items if it.order_item_id == order_items[-1].id)
    assert alco_discount_item.distributed_discount == 140


def test_distributed_discount_should_consider_discount_threshold_when_alco_products_and_no_purchase_price():
    discount_value = 400
    order_items = [
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.regular, actual_price=100, quantity=4),
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.alcohol, actual_price=100, quantity=4),
    ]
    purchase_prices_mapper = {}
    discount = calculate_order_distributed_discount(
        discount_value=discount_value,
        order_items=order_items,
        purchase_prices_mapper=purchase_prices_mapper,
    )
    assert discount.value == 200 + 140
    alco_discount_item = next(it for it in discount.items if it.order_item_id == order_items[-1].id)
    assert alco_discount_item.distributed_discount == 140


def test_distributed_discount_should_consider_when_all_alco():
    discount_value = 400
    order_items = [
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.alcohol, actual_price=100, quantity=4),
        OrderItem(id=uuid4(), product_id=uuid4(), product_type=ProductType.alcohol, actual_price=100, quantity=4),
    ]
    purchase_prices_mapper = {
        order_items[0].product_id: 90,
        order_items[1].product_id: 80,
    }
    discount = calculate_order_distributed_discount(
        discount_value=discount_value,
        order_items=order_items,
        purchase_prices_mapper=purchase_prices_mapper,
    )
    assert discount.value == 40 + 80
    # alco_discount_item = next(it for it in discount.items if it.order_item_id == order_items[-1].id)
    # assert alco_discount_item.distributed_discount == 140
