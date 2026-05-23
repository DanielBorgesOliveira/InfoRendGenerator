from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable
from unicodedata import category, normalize

from info_rend_generator.domain.money import quantize_money


@dataclass(frozen=True)
class Transaction:
    date: datetime
    trntype: str
    amount: Decimal
    name: str
    memo: str


def contains_all(text: str, keywords: Iterable[str]) -> bool:
    normalized_text = normalize_text(text)
    return all(
        normalize_text(keyword) in normalized_text for keyword in keywords if keyword.strip()
    )


def normalize_text(text: str) -> str:
    decomposed = normalize("NFKD", str(text))
    without_accents = "".join(char for char in decomposed if category(char) != "Mn")
    return without_accents.upper()


def sum_transactions(
    transactions: Iterable[Transaction],
    keywords: list[str],
    positive: bool | None = None,
    year: int | None = None,
) -> Decimal:
    total = Decimal("0.00")
    for transaction in transactions:
        if year and transaction.date.year != year:
            continue
        if positive is True and transaction.amount <= 0:
            continue
        if positive is False and transaction.amount >= 0:
            continue

        haystack = f"{transaction.name} {transaction.memo}"
        if keywords and not contains_all(haystack, keywords):
            continue

        total += abs(transaction.amount)

    return quantize_money(total)
