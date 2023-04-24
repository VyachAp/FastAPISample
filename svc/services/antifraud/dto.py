from dataclasses import dataclass
from uuid import UUID


@dataclass
class PromotionUserUniqueDeviceIdentifierDTO:
    id: int
    user_id: UUID
    unique_device_identifier: str
