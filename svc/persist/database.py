import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from svc.settings import DbSettings, get_service_settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_settings: DbSettings):
        self._settings = db_settings
        self.engine: AsyncEngine = self._create_engine(db_settings)

    # def _create_url(self):
    #     url = sqlalchemy.engine.url.URL.create(
    #         DIALECT,
    #         username=config.username,
    #         password=config.password,
    #         host=config.hostname,
    #         port=config.port,
    #         database=config.dbname
    #     )

    @staticmethod
    def _create_engine(settings: DbSettings) -> AsyncEngine:
        logger.debug(f"Connect to database {settings.base_name} at {settings.host}")
        return create_async_engine(
            settings.url,
            pool_size=settings.pool_size,
            pool_pre_ping=True,
            echo=settings.echo,
        )

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        if self.engine is None:
            raise RuntimeError("Uninitialized database")
        await self.engine.dispose()

    async def connection(self) -> AsyncGenerator[AsyncConnection, None]:
        if self.engine is None:
            raise RuntimeError("Uninitialized database")

        async with self.engine.connect() as connection:
            yield connection


database = Database(get_service_settings().db)
conditions_database = Database(get_service_settings().conditions_db)
