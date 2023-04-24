from uuid import UUID

from fastapi import Depends

from svc.infrastructure.catalog.client import CatalogClient
from svc.infrastructure.catalog.models import CategoryListRequest, CategoryModel


class CatalogManager:
    def __init__(
        self,
        catalog_client: CatalogClient = Depends(CatalogClient.instance),
    ) -> None:
        self._catalog_client = catalog_client

    async def get_categories(self, category_ids: list[UUID]) -> list[CategoryModel]:
        if not category_ids:
            return []

        request = CategoryListRequest(category_ids=category_ids, limit=len(category_ids))
        response = await self._catalog_client.get_categories(request)

        if response.error is not None:
            raise Exception(response.error.code)

        if response.result is None:
            return []

        return response.result.items
