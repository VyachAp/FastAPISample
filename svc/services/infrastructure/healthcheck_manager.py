from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text

from svc.persist.database import database


class HealthcheckManager:
    def __init__(self, connection: AsyncConnection = Depends(database.connection)):
        self._connection = connection

    async def check_db(self) -> None:
        (await self._connection.execute(text("SELECT 1"))).first()
