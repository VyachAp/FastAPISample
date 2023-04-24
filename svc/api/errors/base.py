from typing import Optional

from svc.api.models.error_code import ErrorCode


class ApiError(Exception):
    def __init__(self, code: ErrorCode, data: Optional[dict] = None):
        self.code = code
        self.data = data
