from uuid import UUID

from fastapi import Depends
from warehouse.api_client.client import WarehouseGeneralClient
from warehouse.models.warehouse import WarehouseListFilters, WarehouseModel

from svc.api.errors.warehouse import WarehouseNotFoundError
from svc.infrastructure.warehouse.models import WarehouseShortModel


class WarehouseManager:
    def __init__(
        self,
        warehouse_client: WarehouseGeneralClient = Depends(WarehouseGeneralClient.instance),
    ) -> None:
        self._warehouse_client = warehouse_client

    async def get_warehouses(self, warehouse_ids: list[UUID]) -> list[WarehouseModel]:
        if not warehouse_ids:
            return []

        response = await self._warehouse_client.warehouse.list_warehouses(
            WarehouseListFilters(
                warehouse_ids=warehouse_ids,
                offset=0,
                limit=len(warehouse_ids),
            )
        )

        if response.error is not None:
            raise Exception(response.error.code)

        if not response.result:
            return []

        return response.result.items

    async def get_single_warehouse(self, warehouse_id: UUID) -> WarehouseShortModel:
        response = await self._warehouse_client.warehouse.get_warehouse(warehouse_id=warehouse_id)
        if response.error is not None:
            raise Exception(response.error.code)

        if not response.result:
            raise WarehouseNotFoundError()

        res: WarehouseModel = response.result
        return WarehouseShortModel(
            id=res.id,
            active=res.active,
            tz=res.tz,
        )
