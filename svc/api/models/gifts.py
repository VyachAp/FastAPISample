from enum import Enum
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import NonNegativeInt, StrictInt

from .base_model import ApiModel


class CartBannerStyle(Enum):
    info = "info"
    done = "done"

    @classmethod
    def from_db_type(cls, db_value: Literal[1, 2]) -> "CartBannerStyle":
        if db_value == 1:
            return CartBannerStyle.info
        elif db_value == 2:
            return CartBannerStyle.done
        else:
            raise ValueError(f"Wrong db_value for CartBannerStyle: {db_value}")


class BannerInfo(ApiModel):
    id: int
    img_url: str
    style: CartBannerStyle
    title: str
    description: Optional[str]
    btn_text: Optional[str]


class GiftItem(ApiModel):
    product_id: UUID
    quantity: StrictInt


class BaseRequest(ApiModel):
    warehouse_id: UUID
    order_subtotal: NonNegativeInt


class GetGiftRequest(BaseRequest):
    ...


class GetBannerRequest(BaseRequest):
    ...


class GiftDetails(ApiModel):
    gifts_chain: List[GiftItem]
    gift_settings_id: Optional[int]


class BannerDetails(ApiModel):
    banner: Optional[BannerInfo]
