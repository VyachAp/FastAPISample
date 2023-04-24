from datetime import datetime

import pytz
from pydantic import BaseModel, Field


class Message(BaseModel):
    event: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
