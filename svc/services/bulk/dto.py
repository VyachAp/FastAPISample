from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from svc.api.models.bulk import (
    BulkCouponModel,
    BulkCouponValueModel,
    BulkOperation,
    BulkResultModel,
    CategoriesNotFoundError,
    CouponNotFoundError,
    TextError,
    UsersNotFoundError,
    WarehousesNotFoundError,
)

CouponError = WarehousesNotFoundError | CategoriesNotFoundError | UsersNotFoundError | TextError
CouponValueError = CouponNotFoundError | TextError


@dataclass
class BulkCouponRecord:
    data: BulkCouponModel
    coupon_id: Optional[UUID] = None
    operation: Optional[BulkOperation] = None
    errors: list[CouponError] = field(default_factory=list)
    warnings: list[CouponError] = field(default_factory=list)
    applied_at: Optional[datetime] = None

    valid_users: Optional[list[UUID]] = None
    valid_warehouses: Optional[list[UUID]] = None
    valid_categories: Optional[list[UUID]] = None

    @property
    def has_errors(self) -> bool:
        return not not self.errors

    def to_bulk_result(self) -> BulkResultModel:
        return BulkResultModel(
            bulk_item_id=self.data.bulk_item_id,
            operation=self.operation or BulkOperation.create,
            errors=self.errors if self.errors else None,
            warnings=self.warnings if self.warnings else None,
            applied_at=self.applied_at,
        )

    @classmethod
    def from_models(cls, models: list[BulkCouponModel]) -> list["BulkCouponRecord"]:
        return [BulkCouponRecord(data=model) for model in models]


@dataclass
class BulkCouponValueRecord:
    data: BulkCouponValueModel
    coupon_id: Optional[UUID] = None
    operation: Optional[BulkOperation] = None
    errors: list[CouponValueError] = field(default_factory=list)
    warnings: list[CouponValueError] = field(default_factory=list)
    applied_at: Optional[datetime] = None

    @property
    def has_errors(self) -> bool:
        return not not self.errors

    def to_bulk_result(self) -> BulkResultModel:
        return BulkResultModel(
            bulk_item_id=self.data.bulk_item_id,
            operation=self.operation or BulkOperation.create,
            errors=self.errors if self.errors else None,
            warnings=self.warnings if self.warnings else None,
            applied_at=self.applied_at,
        )

    @classmethod
    def from_models(cls, models: list[BulkCouponValueModel]) -> list["BulkCouponValueRecord"]:
        return [BulkCouponValueRecord(data=model) for model in models]
