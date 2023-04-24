from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Annotated, Generic, Literal, Optional, TypeVar, Union
from uuid import UUID, uuid4

from pydantic import Field, PositiveInt, StrictBool

from .base_model import ApiModel
from .coupon import CouponKind


class BulkOperation(str, Enum):
    create = "create"
    update = "update"


class BulkCouponModel(ApiModel):
    """
    value: always divides by 100 regardless of the kind of coupon
    """

    class Config:
        anystr_strip_whitespace = True

    bulk_item_id: UUID = Field(default_factory=uuid4)

    name: str
    active: StrictBool
    value: PositiveInt  # cents or (percent * 100)
    kind: CouponKind
    valid_till: Optional[datetime]
    quantity: Optional[PositiveInt]
    limit: Optional[PositiveInt]
    minimum_order_amount: Optional[PositiveInt]  # cents
    orders_from: Optional[PositiveInt]
    orders_to: Optional[PositiveInt]
    max_discount: Optional[PositiveInt]  # cents
    users: Optional[list[UUID]]
    categories: Optional[list[UUID]]
    warehouses: Optional[list[UUID]]


class BulkCouponValueModel(ApiModel):
    class Config:
        anystr_strip_whitespace = True

    bulk_item_id: UUID = Field(default_factory=uuid4)

    coupon_name: str
    value: PositiveInt  # cents / percent
    orders_number: PositiveInt


TE = TypeVar("TE")


class BulkErrorBase(ABC, ApiModel, Generic[TE]):
    code: str
    data: TE


class DuplicatedItemError(BulkErrorBase[UUID]):
    code: Literal["duplicated_item"] = Field("duplicated_item", const=True)


class WarehousesNotFoundError(BulkErrorBase[list[UUID]]):
    code: Literal["warehouses_not_found"] = Field("warehouses_not_found", const=True)


class CategoriesNotFoundError(BulkErrorBase[list[UUID]]):
    code: Literal["categories_not_found"] = Field("categories_not_found", const=True)


class UsersNotFoundError(BulkErrorBase[list[UUID]]):
    code: Literal["users_not_found"] = Field("users_not_found", const=True)


class CouponNotFoundError(BulkErrorBase[str]):
    code: Literal["coupon_not_found"] = Field("coupon_not_found", const=True)


class TextError(BulkErrorBase[str]):
    code: Literal["text_error"] = Field("text_error", const=True)


BulkError = Annotated[
    Union[
        DuplicatedItemError,
        WarehousesNotFoundError,
        CategoriesNotFoundError,
        UsersNotFoundError,
        CouponNotFoundError,
        TextError,
    ],
    Field(discriminator="code"),
]


class BulkResultModel(ApiModel):
    bulk_item_id: UUID
    operation: BulkOperation
    errors: Optional[list[BulkError]]
    warnings: Optional[list[BulkError]]
    applied_at: Optional[datetime]


class BulkCouponRequest(ApiModel):
    items: list[BulkCouponModel]


class BulkCouponValueRequest(ApiModel):
    items: list[BulkCouponValueModel]


class BulkResponse(ApiModel):
    items: list[BulkResultModel]
