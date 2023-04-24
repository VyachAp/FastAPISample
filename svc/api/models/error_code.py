from enum import Enum


class ErrorCode(str, Enum):
    coupon_not_found = "coupon_not_found"
    coupon_not_valid = "coupon_not_valid"
    coupon_not_permitted_user = "coupon_not_permitted_user"
    coupon_not_permitted_categories = "coupon_not_permitted_categories"
    coupon_min_amount = "coupon_min_amount"
    coupon_not_permitted_warehouse = "coupon_not_permitted_warehouse"
    referral_coupon_self_usage = "referral_coupon_self_usage"
    referral_coupon_limit = "referral_coupon_limit"
    coupon_redeemed = "coupon_redeemed"
    coupon_redeemed_limit = "coupon_redeemed_limit"
    coupon_redeemed_orders_to = "coupon_redeemed_orders_to"
    coupon_redeemed_orders_from = "coupon_redeemed_orders_from"
    gift_settings_not_found = "gift_settings_not_found"
    gift_settings_min_sum = "gift_settings_min_sum"
    user_not_eligible_to_use_coupon = "user_not_eligible_to_use_coupon"
    warehouse_not_found = "warehouse_not_found"
