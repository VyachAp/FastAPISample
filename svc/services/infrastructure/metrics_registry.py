from functools import lru_cache
from typing import Optional
from uuid import UUID

from prometheus_client import Counter


class MetricsRegistry:
    _antifraud_coupon_bans = Counter(
        "antifraud_coupon_bans", "Count coupon usage bans", ["user_id", "fingerprint"], namespace="promotion"
    )
    _whitelisted_user_antifraud_coupon_usage = Counter(
        "whitelisted_user_antifraud_coupon_usage",
        "Count whitelisted user coupon usage",
        ["user_id", "fingerprint"],
        namespace="promotion",
    )
    _whitelisted_fingerprint_antifraud_coupon_usage = Counter(
        "whitelisted_fingerprint_antifraud_coupon_usage",
        "Count whitelisted fingerprint coupon usage",
        ["user_id", "fingerprint"],
        namespace="promotion",
    )

    def register_antifraud_coupon_ban(self, user_id: UUID, fingerprint: Optional[str]) -> None:
        self._antifraud_coupon_bans.labels(user_id=str(user_id), fingerprint=fingerprint).inc()

    def register_whitelisted_user_antifraud_coupon_usage(self, user_id: UUID, fingerprint: Optional[str]) -> None:
        self._whitelisted_user_antifraud_coupon_usage.labels(user_id=str(user_id), fingerprint=fingerprint).inc()

    def register_whitelisted_fingerprint_antifraud_coupon_usage(
        self, user_id: UUID, fingerprint: Optional[str]
    ) -> None:
        self._whitelisted_fingerprint_antifraud_coupon_usage.labels(user_id=str(user_id), fingerprint=fingerprint).inc()


@lru_cache
def get_metrics_registry() -> MetricsRegistry:
    return MetricsRegistry()
