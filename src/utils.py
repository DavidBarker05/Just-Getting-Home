from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def nearest_int(value: float) -> int:
    # Avoid Python's banker rounding surprises for pixel math.
    return int(value + 0.5)


def first_of(value: T | None, fallback: T) -> T:
    return fallback if value is None else value

