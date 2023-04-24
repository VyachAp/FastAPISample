from typing import Dict, Optional

from svc.api.errors.base import ApiError
from svc.api.models.error_code import ErrorCode


class GiftSettingsNotFoundError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.gift_settings_not_found, data)


class GiftSettingsMinSumError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.gift_settings_min_sum, data)
