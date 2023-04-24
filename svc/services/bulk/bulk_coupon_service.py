import asyncio
from uuid import UUID

from fastapi import Depends

from svc.api.models.bulk import (
    BulkCouponModel,
    BulkCouponValueModel,
    BulkOperation,
    BulkResultModel,
    CategoriesNotFoundError,
    CouponNotFoundError,
    DuplicatedItemError,
    UsersNotFoundError,
    WarehousesNotFoundError,
)
from svc.infrastructure.catalog.catalog_manager import CatalogManager
from svc.infrastructure.customer.customer_profile_manager import CustomerProfileManager
from svc.infrastructure.warehouse.warehouse_manager import WarehouseManager
from svc.services.bulk.bulk_coupon_manager import BulkCouponManager
from svc.services.bulk.dto import BulkCouponRecord, BulkCouponValueRecord
from svc.services.uow import UnitOfWork


class BulkCouponService:
    def __init__(
        self,
        uow: UnitOfWork = Depends(UnitOfWork),
        bulk_coupon_manager: BulkCouponManager = Depends(BulkCouponManager),
        warehouse_manager: WarehouseManager = Depends(WarehouseManager),
        customer_manager: CustomerProfileManager = Depends(CustomerProfileManager),
        catalog_manager: CatalogManager = Depends(CatalogManager),
    ) -> None:
        self._uow = uow
        self._bulk_coupon_manager = bulk_coupon_manager
        self._warehouse_manager = warehouse_manager
        self._customer_manager = customer_manager
        self._catalog_manager = catalog_manager

    async def save_coupons(self, items: list[BulkCouponModel]) -> list[BulkResultModel]:

        records = BulkCouponRecord.from_models(items)
        records_map = dict[str, BulkCouponRecord]()
        for record in records:
            key = record.data.name.lower()
            if (prev_value := records_map.get(key)) is not None:
                prev_value.errors.append(DuplicatedItemError(data=record.data.bulk_item_id))

            records_map[key] = record

        await asyncio.gather(
            self._validate_users(records),
            self._validate_warehouses(records),
            self._validate_categories(records),
        )

        to_upsert = [record for record in records if record.has_errors is False]
        async with self._uow.begin():
            await self._bulk_coupon_manager.bulk_upsert(items=to_upsert)
            await self._bulk_coupon_manager.overwrite_warehouses(to_upsert)
            await self._bulk_coupon_manager.overwrite_users(to_upsert)
            await self._bulk_coupon_manager.overwrite_categories(to_upsert)

        return [record.to_bulk_result() for record in records]

    async def save_coupon_values(self, items: list[BulkCouponValueModel]) -> list[BulkResultModel]:
        records = BulkCouponValueRecord.from_models(items)
        records_map = dict[tuple[str, int], BulkCouponValueRecord]()

        coupon_names = set[str]()
        for record in records:
            coupon_name = record.data.coupon_name.lower()
            coupon_names.add(coupon_name)
            key = (coupon_name, record.data.orders_number)
            record.operation = BulkOperation.create

            if (prev_value := records_map.get(key)) is not None:
                prev_value.errors.append(DuplicatedItemError(data=record.data.bulk_item_id))

            records_map[key] = record

        async with self._uow.begin():
            existing_coupons = await self._bulk_coupon_manager.get_coupons_name_map(
                list(coupon_names),
                locked=True,
            )
            to_create = list[BulkCouponValueRecord]()

            for (coupon_name, _), record in records_map.items():
                if record.has_errors:
                    continue

                coupon_id = existing_coupons.get(coupon_name)
                if coupon_id is None:
                    record.errors.append(CouponNotFoundError(data=coupon_name))
                    continue

                record.coupon_id = coupon_id
                to_create.append(record)

            if to_create:
                await self._bulk_coupon_manager.overwrite_coupon_values(to_create)

        return [record.to_bulk_result() for record in records]

    async def _validate_users(self, items: list[BulkCouponRecord]) -> None:
        user_ids = set[UUID]()
        for item in items:
            if not item.data.users:
                continue

            for user_id in item.data.users:
                user_ids.add(user_id)

        if not user_ids:
            return

        users = await self._customer_manager.get_customers(list(user_ids))
        users_map = {user.id: user for user in users}

        for item in items:
            if not item.data.users:
                continue

            invalid_ids = list[UUID]()
            valid_ids = list[UUID]()
            for user_id in item.data.users:
                user = users_map.get(user_id)
                if user is None:
                    invalid_ids.append(user_id)
                else:
                    valid_ids.append(user_id)

            if invalid_ids:
                item.warnings.append(UsersNotFoundError(data=invalid_ids))

            if valid_ids:
                item.valid_users = valid_ids

    async def _validate_warehouses(self, items: list[BulkCouponRecord]) -> None:
        warehouse_ids = set[UUID]()
        for item in items:
            if not item.data.warehouses:
                continue

            for warehouse_id in item.data.warehouses:
                warehouse_ids.add(warehouse_id)

        if not warehouse_ids:
            return

        warehouses = await self._warehouse_manager.get_warehouses(list(warehouse_ids))
        warehouses_map = {warehouse.id: warehouse for warehouse in warehouses}

        for item in items:
            if not item.data.warehouses:
                continue

            invalid_ids = list[UUID]()
            valid_ids = list[UUID]()
            for warehouse_id in item.data.warehouses:
                warehouse = warehouses_map.get(warehouse_id)
                if warehouse is None:
                    invalid_ids.append(warehouse_id)
                else:
                    valid_ids.append(warehouse_id)

            if invalid_ids:
                item.warnings.append(WarehousesNotFoundError(data=invalid_ids))

            if valid_ids:
                item.valid_warehouses = valid_ids

    async def _validate_categories(self, items: list[BulkCouponRecord]) -> None:
        category_ids = set[UUID]()
        for item in items:
            if not item.data.categories:
                continue

            for category_id in item.data.categories:
                category_ids.add(category_id)

        if not category_ids:
            return

        categories = await self._catalog_manager.get_categories(list(category_ids))
        categories_map = {category.id: category for category in categories}

        for item in items:
            if not item.data.categories:
                continue

            invalid_ids = list[UUID]()
            valid_ids = list[UUID]()
            for category_id in item.data.categories:
                category = categories_map.get(category_id)
                if category is None:
                    invalid_ids.append(category_id)
                else:
                    valid_ids.append(category_id)

            if invalid_ids:
                item.warnings.append(CategoriesNotFoundError(data=invalid_ids))

            if valid_ids:
                item.valid_categories = valid_ids
