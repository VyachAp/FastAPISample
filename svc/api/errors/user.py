from typing import Dict, Optional

from svc.api.errors.base import ApiError
from svc.api.models.error_code import ErrorCode


class UserNotEligibleToUseCoupon(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.user_not_eligible_to_use_coupon, data)
