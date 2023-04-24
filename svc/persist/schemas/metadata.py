import datetime

from sqlalchemy import Column, DateTime, MetaData, Table, TypeDecorator

__all__ = [
    "PublicSchema",
    "TZDateTime",
]

from sqlalchemy.engine import Dialect


class PublicSchema(type):
    metadata = MetaData(schema="public")
    __table__ = None

    def __init__(cls, name, bases, dct):  # type: ignore[no-untyped-def]
        columns = []
        for attr in cls.__dict__.values():
            if isinstance(attr, Column):
                columns.append(attr)

        cls.table = Table(cls.__table__, cls.metadata, *columns)


class TZDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(  # type:ignore[override]
        self,
        value: datetime.datetime,
        dialect: Dialect,
    ) -> datetime.datetime:
        if value is not None:
            value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        return value

    def process_result_value(self, value: datetime.datetime, dialect: Dialect) -> datetime.datetime:
        if value is not None:
            value = value.replace(tzinfo=datetime.timezone.utc)

        return value
