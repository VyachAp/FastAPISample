from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, overload

ROUNDING_PRECISION = Decimal(".01")


@overload
def dollars_to_cents(value: None) -> None:
    ...


@overload
def dollars_to_cents(value: Decimal) -> int:
    ...


def dollars_to_cents(value: Optional[Decimal]) -> Optional[int]:
    if value is None:
        return None

    return int(value.quantize(ROUNDING_PRECISION, ROUND_HALF_UP) * 100)


@overload
def cents_to_dollars(value: None) -> None:
    ...


@overload
def cents_to_dollars(value: int) -> Decimal:
    ...


def cents_to_dollars(value: Optional[int]) -> Optional[Decimal]:
    if value is None:
        return None

    return (Decimal(value) / Decimal("100.0")).quantize(ROUNDING_PRECISION, ROUND_HALF_UP)
