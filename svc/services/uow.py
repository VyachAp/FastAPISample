from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from svc.persist.database import conditions_database, database


class BaseUnitOfWork:
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator:
        if self._connection.in_transaction():
            await self._connection.commit()

        async with self._connection.begin():
            yield


class UnitOfWork(BaseUnitOfWork):
    def __init__(self, connection: AsyncConnection = Depends(database.connection)):
        super().__init__(connection)


class ConditionsUnitOfWork(BaseUnitOfWork):
    def __init__(self, connection: AsyncConnection = Depends(conditions_database.connection)):
        super().__init__(connection)
