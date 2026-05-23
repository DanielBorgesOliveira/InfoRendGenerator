from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional


def quantize_money(value: Decimal | float | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_money(value: Decimal | float | str) -> str:
    amount = quantize_money(value)
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_money(value: Optional[str]) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    normalized = value.strip().replace(".", "").replace(",", ".")
    return quantize_money(normalized)
