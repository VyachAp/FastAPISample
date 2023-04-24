from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field


class LoggingProfileEnum(Enum):
    debug = "debug"
    production = "production"
    testing = "testing"


class DbSettings(BaseSettings):
    username: str = "svc"
    password: str = "qwerty123"
    host: str = "localhost"
    base_name: str = "main"
    port: int = 5432
    pool_size: int = 5
    echo: bool = False

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.base_name}"

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.base_name}"

    class Config:
        env_prefix = "db_"


class ConditionsDbSettings(DbSettings):
    class Config:
        env_prefix = "conditions_db_"


class KafkaSettings(BaseSettings):
    bootstrap: str = "localhost:9092"
    group_id: str = "promotion"
    max_request_size: int = 1048576

    class Config:
        env_prefix = "kafka_"


class TracingSettings(BaseSettings):
    jaeger_enabled: bool = False
    jaeger_agent_host_name: Optional[str] = None
    jaeger_agent_port: Optional[int] = None
    jaeger_collector_endpoint: Optional[str] = None

    zipkin_enabled: bool = False
    zipkin_endpoint: Optional[str] = None

    console_enabled: bool = False

    sampling_rate: float = 0.1

    class Config:
        env_prefix = "trace_"


class ReferralCouponConfig(BaseSettings):
    initial_orders_count_permit: int = Field(2, gt=0)
    kind: int = 1
    value: int = 250
    max_discount: Optional[int] = None
    quantity: Optional[int] = None
    limit: Optional[int] = None
    minimum_order_amount: Optional[int] = None

    class Config:
        env_prefix = "referral_coupon_"


class UserAntifraudConfig(BaseSettings):
    check_enabled: bool = True
    amount_of_users_per_fingerprint: int = 3

    class Config:
        env_prefix = "user_antifraud_"


class CacheRegistryConfig(BaseSettings):
    warehouses_ttl: int = 60 * 60

    class Config:
        env_prefix = "cache_"


@lru_cache
def get_cache_config() -> CacheRegistryConfig:
    return CacheRegistryConfig()


class CacheDistributedRegistryConfig(BaseSettings):
    purchase_price_ttl: int = 10 * 60
    url: str = "memory://"

    class Config:
        env_prefix = "cache_distributed_"


@lru_cache
def get_distributed_cache_config() -> CacheDistributedRegistryConfig:
    return CacheDistributedRegistryConfig()


class ProgressBarMessages(BaseSettings):
    placeholders: str = ""
    placeholders_split_char = "\n"

    first_bar_title: str = ""
    first_bar_subtitle: Optional[str] = None

    second_bar_title: str = ""
    second_bar_subtitle: Optional[str] = None

    @property
    def placeholders_split(self) -> List[str]:
        return self.placeholders.split(self.placeholders_split_char)


class OrderBonusSettings(BaseSettings):
    max_free_small_orders: int = 3
    progress_bar_image_info: Optional[
        str
    ] = None
    progress_bar_image_bonus: Optional[str] = None

    small_order_fee_no_bonus: ProgressBarMessages = ProgressBarMessages(
        first_bar_title="Add ${remaining_amount:4.2f} to avoid small order fee",
    )

    small_order_fee_no_bonus_passed: ProgressBarMessages = ProgressBarMessages(
        placeholders="Yay, no small order fee",
    )

    small_order_with_bonus_empty: ProgressBarMessages = ProgressBarMessages(
        placeholders="Add ${remaining_amount:4.2f} to get {bonus_amount} off"
    )

    small_order_with_bonus_first_title: ProgressBarMessages = ProgressBarMessages(
        first_bar_title="Add ${remaining_amount:4.2f} to avoid small order fee"
    )

    small_order_with_bonus_second_title: ProgressBarMessages = ProgressBarMessages(
        second_bar_title="Add ${remaining_amount:4.2f} to get {bonus_amount} off",
    )

    small_order_with_bonus_double_title: ProgressBarMessages = ProgressBarMessages(
        first_bar_title="No small order fee!",
        second_bar_title="Add ${remaining_amount:4.2f} to get {bonus_amount} off",
    )

    small_order_with_bonus_on: ProgressBarMessages = ProgressBarMessages(
        placeholders="Yay, {bonus_amount} off your order",
    )

    small_order_happy_empty: ProgressBarMessages = ProgressBarMessages(
        placeholders="Yay, it's happy hour. Add ${remaining_amount:4.2f} to get {bonus_amount} off"
    )

    small_order_happy_no_bonus: ProgressBarMessages = ProgressBarMessages(
        first_bar_title="Add ${remaining_amount:4.2f} to get {bonus_amount} off"
    )

    small_order_happy_fee: ProgressBarMessages = ProgressBarMessages(
        first_bar_title="Add ${remaining_amount:4.2f} to avoid small order fee"
    )

    small_order_happy_no_fee_catalog = ProgressBarMessages(
        first_bar_title="No small order fee!",
        second_bar_title="Add ${remaining_amount:4.2f} more to get {bonus_amount} off",
    )

    small_order_happy_no_fee_cart = ProgressBarMessages(
        second_bar_title="Add ${remaining_amount:4.2f} more to get {bonus_amount} off"
    )

    small_order_happy_on: ProgressBarMessages = ProgressBarMessages(placeholders="Yay, {bonus_amount} off your order")

    class Config:
        env_prefix = "order_bonus_settings_"


class ConditionsSettings(BaseSettings):
    order_conditions_image: Optional[str] = None
    conditions_delivery_image: Optional[
        str
    ] = None
    conditions_bonus_image: Optional[str] = None
    conditions_gift_image: Optional[str] = ""

    first_free_delivery_title: str = "$0.00 delivery fee on your first {free_orders_count} orders"
    first_free_delivery_subtitle: str = (
        "${delivery_fee_amount:4.2f} delivery fee amount for all other orders under ${fee_subtotal:4.2f}"
    )

    delivery_fee_title: str = "Delivery fee is ${delivery_fee_amount:4.2f}"
    delivery_fee_active_subtitle: str = "$0.00 for orders with subtotal over ${fee_subtotal:4.2f}"
    delivery_fee_free_subtitle: str = "Your subtotal is over ${fee_subtotal:4.2f}"

    large_bonus_image: Optional[str] = None
    large_bonus_color: Optional[str] = None

    large_bonus_active_title: str = "{bonus_amount} off your order"
    large_bonus_title: str = "Just spend ${remaining_amount:4.2f} more and get {bonus_amount} off your order"

    large_bonus_subtitle: Optional[str] = None

    conditions_small_order_fee_title = "No small order fee for subtotal over ${required_amount:4.2f}"

    conditions_small_order_fee_subtitle = "Small order fee is ${fee_amount:4.2f}"

    conditions_bonus_title: str = "{bonus_amount} off bonus for subtotal over ${required_amount:4.2f}"

    conditions_bonus_subtitle: str = "* Discounts do not apply on alcohol and tobacco products"

    conditions_gift_title = "Gift for subtotal over ${required_amount:4.2f}"

    class Config:
        env_prefix = "conditions_settings_"


class Settings(BaseSettings):
    db: DbSettings = DbSettings()
    conditions_db: ConditionsDbSettings = ConditionsDbSettings()
    tracing: TracingSettings = TracingSettings()
    logging_profile: LoggingProfileEnum = LoggingProfileEnum.debug
    kafka: KafkaSettings = KafkaSettings()

    order_bonus_settings: OrderBonusSettings = OrderBonusSettings()
    order_conditions_settings: ConditionsSettings = ConditionsSettings()

    referral_coupon: ReferralCouponConfig = ReferralCouponConfig()
    user_antifraud: UserAntifraudConfig = UserAntifraudConfig()
    min_order_amount: int = 50


@lru_cache
def get_service_settings() -> Settings:
    return Settings()
