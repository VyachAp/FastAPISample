from uuid import UUID

from fastapi import Depends

from svc.infrastructure.warehouse.models import WarehouseShortModel
from svc.infrastructure.warehouse.warehouse_manager import WarehouseManager
from svc.services.cache import LocalCacheRegistry


class WarehouseAdapter:
    def __init__(
        self,
        warehouse_manager: WarehouseManager = Depends(WarehouseManager),
        cache_registry: LocalCacheRegistry = Depends(LocalCacheRegistry),
    ) -> None:
        self._warehouse_manager = warehouse_manager
        self._cache = cache_registry

    async def get_warehouse(self, warehouse_id: UUID) -> WarehouseShortModel:
        result = await self._cache.warehouses.get(warehouse_id)
        if result is None:
            warehouse: WarehouseShortModel = await self._warehouse_manager.get_single_warehouse(warehouse_id)
            await self._cache.warehouses.set(warehouse_id, warehouse)
            return warehouse

        return result
