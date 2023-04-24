from uuid import UUID

from sqlalchemy.engine import Row

from svc.api.models.gifts import CartBannerStyle
from svc.persist.schemas.gift import CartBannerSchema, GiftProductSchema, GiftPromotionSettingsSchema
from svc.services.gift.dto import CartBannerModel, GiftChoice, GiftProductModel, GiftPromotionSettingsModel
from svc.utils.money import dollars_to_cents


class GiftPromotionSettingsMapper:
    @classmethod
    def map_to_model(cls, entity: Row) -> GiftPromotionSettingsModel:
        return GiftPromotionSettingsModel(
            id=entity[GiftPromotionSettingsSchema.id],
            active=entity[GiftPromotionSettingsSchema.active],
            warehouse_id=entity[GiftPromotionSettingsSchema.warehouse_id],
            name=entity[GiftPromotionSettingsSchema.name],
            date_from=entity[GiftPromotionSettingsSchema.date_from],
            date_till=entity[GiftPromotionSettingsSchema.date_till],
            min_sum=dollars_to_cents(entity[GiftPromotionSettingsSchema.min_sum]),
            less_sum_banner_id=entity[GiftPromotionSettingsSchema.less_sum_banner_id],
            greater_sum_banner_id=entity[GiftPromotionSettingsSchema.greater_sum_banner_id],
            created_at=entity[GiftPromotionSettingsSchema.created_at],
            updated_at=entity[GiftPromotionSettingsSchema.updated_at],
        )


class GiftProductMapper:
    @classmethod
    def map_to_model(cls, entity: Row) -> GiftProductModel:
        return GiftProductModel(
            id=entity[GiftProductSchema.id],
            gift_promotion_settings_id=entity[GiftProductSchema.gift_promotion_settings_id],
            products_chain=[
                GiftChoice(
                    product_id=UUID(it["product_id"]),
                    quantity=it["quantity"],
                )
                for it in entity[GiftProductSchema.products_chain]
            ],
            created_at=entity[GiftProductSchema.created_at],
            updated_at=entity[GiftProductSchema.updated_at],
        )


class CartBannerMapper:
    @classmethod
    def map_to_model(cls, entity: Row) -> CartBannerModel:
        style = CartBannerStyle.from_db_type(entity[CartBannerSchema.style])

        return CartBannerModel(
            id=entity[CartBannerSchema.id],
            image_url=entity[CartBannerSchema.image_url],
            style=style,
            title=entity[CartBannerSchema.title],
            description=entity[CartBannerSchema.description],
            btn_text=entity[CartBannerSchema.btn_text],
            created_at=entity[CartBannerSchema.created_at],
            updated_at=entity[CartBannerSchema.updated_at],
        )
