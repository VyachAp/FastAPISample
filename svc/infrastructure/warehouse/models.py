from dataclasses import dataclass
from uuid import UUID


@dataclass
class WarehouseShortModel:
    id: UUID
    active: bool
    tz: str
