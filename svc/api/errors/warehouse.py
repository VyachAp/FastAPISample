from typing import Dict, Optional

from svc.api.errors.base import ApiError
from svc.api.models.error_code import ErrorCode


class WarehouseNotFoundError(ApiError):
    def __init__(self, data: Optional[Dict] = None) -> None:
        super().__init__(ErrorCode.warehouse_not_found, data)
