from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from svc.api.models.gifts import CartBannerStyle


@dataclass
class GiftPromotionSettingsModel:
    id: int
    active: bool
    warehouse_id: Optional[UUID]
    name: Optional[str]
    date_from: datetime
    date_till: datetime
    min_sum: int
    less_sum_banner_id: Optional[int]
    greater_sum_banner_id: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class GiftChoice:
    product_id: UUID
    quantity: int


@dataclass
class GiftProductModel:
    id: int
    gift_promotion_settings_id: int
    products_chain: List[GiftChoice]
    created_at: datetime
    updated_at: datetime


@dataclass
class CartBannerModel:
    id: int
    image_url: Optional[str]
    style: CartBannerStyle
    title: str
    description: Optional[str]
    btn_text: Optional[str]
    created_at: datetime
    updated_at: datetime
