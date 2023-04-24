from enum import Enum
from typing import Optional
from uuid import UUID

from internal_lib.v2.models import APIModel
from pydantic import Field


class CatalogErrorCode(str, Enum):
    unknown = "unknown"


class CategoryListRequest(APIModel):
    offset: Optional[int]
    limit: Optional[int]
    category_ids: Optional[list[UUID]]


class CategoryModel(APIModel):
    id: UUID
    name: str
    active: bool
    parent_id: Optional[UUID]
    kind: str


class CategoryList(APIModel):
    items: list[CategoryModel] = Field(default_factory=list)
