from typing import Dict, Optional

from svc.api.errors.base import ApiError
from svc.api.models.error_code import ErrorCode


class CouponNotFoundError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_not_found, data)


class CouponNotValidError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_not_valid, data)


class CouponNotPermittedCategoryError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_not_permitted_categories, data)


class CouponNotPermittedUserError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_not_permitted_user, data)


class CouponMinAmountError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_min_amount, data)


class CouponNotPermittedWarehouseError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_not_permitted_warehouse, data)


class ReferralCouponSelfUsageError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.referral_coupon_self_usage, data)


class ReferralCouponLimitError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.referral_coupon_limit, data)


class CouponRedeemedLimitError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_redeemed_limit, data)


class CouponRedeemedOrdersFromError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_redeemed_orders_from, data)


class CouponRedeemedOrdersToError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_redeemed_orders_to, data)


class CouponRedeemedError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.coupon_redeemed, data)
