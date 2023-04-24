from uuid import UUID

from customer_profile.api.models.user import UserCompactModel, UserListFilter
from customer_profile.api_client.client import CustomerProfileClient
from fastapi import Depends


class CustomerProfileManager:
    def __init__(
        self,
        customer_client: CustomerProfileClient = Depends(CustomerProfileClient.instance),
    ) -> None:
        self._customer_client = customer_client

    async def get_customers(self, user_ids: list[UUID]) -> list[UserCompactModel]:
        response = await self._customer_client.search_users(
            UserListFilter(
                offset=0,
                limit=len(user_ids),
                user_ids=user_ids,
            )
        )

        if response.error:
            raise Exception(response.error.code)

        if not response.result:
            return []

        return response.result.items
