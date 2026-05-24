from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from pyqlite.time.daycounter import Actual365Fixed, DayCounter


@dataclass(frozen=True)
class ZeroInflationCurve:
    reference_date: date
    base_index: float
    zero_rate: float
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if self.base_index <= 0.0:
            raise ValueError("base_index must be positive")

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def index_fixing(self, d: date) -> float:
        return self.base_index * math.exp(self.zero_rate * max(self.time_from_reference(d), 0.0))


@dataclass(frozen=True)
class InflationIndexCurve:
    reference_date: date
    dates: tuple[date, ...]
    index_levels: tuple[float, ...]
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.index_levels):
            raise ValueError("dates and index levels must have the same length")
        if not self.dates:
            raise ValueError("at least one inflation index node is required")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("inflation index dates must be sorted")
        if any(level <= 0.0 for level in self.index_levels):
            raise ValueError("inflation index levels must be positive")

    def index_fixing(self, d: date) -> float:
        if d <= self.dates[0]:
            return self.index_levels[0]
        if d >= self.dates[-1]:
            return self.index_levels[-1]
        times = tuple(self.day_counter.year_fraction(self.reference_date, x) for x in self.dates)
        logs = tuple(math.log(x) for x in self.index_levels)
        t = self.day_counter.year_fraction(self.reference_date, d)
        for i in range(1, len(times)):
            if t <= times[i]:
                return math.exp(_linear(times[i - 1], logs[i - 1], times[i], logs[i], t))
        raise RuntimeError("unreachable inflation interpolation state")


def _linear(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 == x0:
        return y1
    return y0 + (x - x0) / (x1 - x0) * (y1 - y0)
