from typing import Generic, TypeVar

from internal_lib.v2.models import APIModel as ApiModel
from internal_lib.v2.models import APIResponse as BaseApiResponse
from internal_lib.v2.models import ErrorResponse as BaseErrorResponse
from internal_lib.v2.models import PaginatedListModel

from .error_code import ErrorCode

__all__ = (
    "ErrorResponse",
    "ApiModel",
    "ApiResponse",
    "PaginatedListModel",
)


class ErrorResponse(BaseErrorResponse[ErrorCode]):
    pass


T = TypeVar("T")


class ApiResponse(BaseApiResponse[T, ErrorCode], Generic[T]):
    pass
