"""Deterministic calculations to support reconciliation."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


def sum_line_items(items: Iterable[str | float | int]) -> float:
    total = Decimal("0")
    for item in items:
        total += Decimal(str(item))
    return float(total)


def compute_tax_from_rate(amount: float, rate: float) -> float:
    return float((Decimal(str(amount)) * Decimal(str(rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def currency_normalize(value: str) -> float:
    cleaned = "".join(ch for ch in value if (ch.isdigit() or ch in {".", "-"}))
    return float(cleaned) if cleaned else 0.0
