from decimal import Decimal

from sqlalchemy.engine import Row

from svc.api.models.coupon import CouponKind
from svc.persist.schemas.coupon import CouponSchema
from svc.services.coupon.dto import CouponModel, CouponType
from svc.utils.money import dollars_to_cents


class CouponMapper:
    @classmethod
    def map_to_model(cls, entity: Row) -> CouponModel:
        kind = CouponKind.from_db_type(entity[CouponSchema.kind])

        return CouponModel(
            id=entity[CouponSchema.id],
            active=entity[CouponSchema.active],
            name=entity[CouponSchema.name],
            description=entity[CouponSchema.description],
            value=cls.calculate_value(entity[CouponSchema.value], kind),
            kind=kind,
            valid_till=entity[CouponSchema.valid_till],
            quantity=entity[CouponSchema.quantity],
            limit=entity[CouponSchema.limit],
            minimum_order_amount=dollars_to_cents(entity[CouponSchema.minimum_order_amount]),
            created_at=entity[CouponSchema.created_at],
            updated_at=entity[CouponSchema.updated_at],
            user_id=entity[CouponSchema.user_id],
            coupon_type=CouponType.from_db_type(entity[CouponSchema.coupon_type]),
            orders_from=entity[CouponSchema.orders_from],
            orders_to=entity[CouponSchema.orders_to],
            max_discount=dollars_to_cents(entity[CouponSchema.max_discount]),
        )

    @classmethod
    def calculate_value(cls, value: Decimal, kind: CouponKind) -> int:
        if kind == CouponKind.percent:
            return int(value)

        return dollars_to_cents(value)
