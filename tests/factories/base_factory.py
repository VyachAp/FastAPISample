import asyncio
import inspect
from types import SimpleNamespace
from typing import Type

import factory
from sqlalchemy import literal_column

from svc.persist.schemas.metadata import PublicSchema


class AsyncFactory(factory.Factory):
    class Meta:
        abstract = True

    @classmethod
    async def create_batch(cls, size, **kwargs):
        return [await cls.create(**kwargs) for _ in range(size)]

    @classmethod
    def _create(cls, model_class: Type[PublicSchema], **kwargs):
        connection = cls._meta.connection

        async def maker_coroutine():
            for key, value in kwargs.items():
                if inspect.isawaitable(value):
                    kwargs[key] = await value

            result = await connection.execute(
                model_class.table.insert().values(**kwargs).returning(literal_column("*"))
            )
            entity = result.fetchone()

            return SimpleNamespace(**entity)

        return asyncio.create_task(maker_coroutine())
