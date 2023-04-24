from datetime import datetime

import factory

from svc.persist.schemas.gift import CartBannerSchema, CartBannerStyleSchema
from tests.factories.base_factory import AsyncFactory


class CartBannerFactory(AsyncFactory):
    class Meta:
        model = CartBannerSchema

    id = factory.Sequence(int)
    image_url = "https://some_img.com/123.png"
    style = 2
    title = "default_title"
    description = None
    btn_text = "press"
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class CartBannerStyleFactory(AsyncFactory):
    class Meta:
        model = CartBannerStyleSchema

    id = factory.Sequence(int)
    name = None
