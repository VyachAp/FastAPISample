from functools import lru_cache

from internal_lib.v2.api_client import APIClient
from internal_lib.v2.models import APIResponse

from svc.infrastructure.catalog.models import CatalogErrorCode, CategoryList, CategoryListRequest
from svc.infrastructure.catalog.settings import CatalogClientSettings


class CatalogClient(APIClient):
    @staticmethod
    @lru_cache
    def instance() -> "CatalogClient":
        settings = CatalogClientSettings()
        return CatalogClient(
            api_url=settings.url,
            service_name="catalog",
            timeout=settings.timeout_seconds,
        )

    def __init__(self, api_url: str, service_name: str, timeout: int):
        super().__init__(api_url, service_name, timeout)

    async def get_categories(self, request: CategoryListRequest) -> APIResponse[CategoryList, CatalogErrorCode]:
        response = await self._send_request(
            "POST",
            url="/categories",
            body=request,
            params=None,
            response_cls=APIResponse[CategoryList, CatalogErrorCode],
        )

        return response
