from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.events.message_handlers import handle_order_canceled, handle_order_paid
from svc.events.messages import OrderCanceledMessage, OrderPaidMessage
from tests.factories.coupon import CouponFactory
from tests.factories.user_coupon import UserCouponFactory

from .helpers import get_coupon, get_user_coupon


class TestOrderPaidMessage:
    @pytest.mark.asyncio
    async def test_default_behaviour(self, db_connection: AsyncConnection) -> None:
        coupon = await CouponFactory.create(quantity=5)
        order_id = uuid4()
        user_id = uuid4()
        user_coupon = await UserCouponFactory(user_id=user_id, coupon_id=coupon.id, order_id=order_id)

        await handle_order_paid(
            OrderPaidMessage(
                order_id=order_id,
            ),
            db_connection,
        )
        # Check DB objects
        db_coupon = await get_coupon(db_connection, coupon_id=coupon.id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            user_coupon_id=user_coupon.id,
        )
        assert db_coupon and db_coupon.quantity == coupon.quantity, "Quantity should stay the same"
        assert db_user_coupon and db_user_coupon.order_paid is True, "UserCoupon.order_paid should be True"


class TestOrderCanceledMessage:
    @pytest.mark.asyncio
    async def test_default_behaviour(self, db_connection: AsyncConnection) -> None:
        coupon = await CouponFactory.create(quantity=5)
        coupon_id = coupon.id
        order_id = uuid4()
        user_id = uuid4()
        user_coupon = await UserCouponFactory(user_id=user_id, coupon_id=coupon_id, order_id=order_id)

        await handle_order_canceled(
            OrderCanceledMessage(
                order_id=order_id,
            ),
            db_connection,
        )
        # Get objects from DB
        db_coupon = await get_coupon(db_connection, coupon_id=coupon_id)
        db_user_coupon = await get_user_coupon(
            db_connection,
            user_coupon_id=user_coupon.id,
        )
        assert db_coupon and db_coupon.quantity - coupon.quantity == 1, "Quantity should be reverted"
        assert not db_user_coupon, "UserCoupon should be deleted"
