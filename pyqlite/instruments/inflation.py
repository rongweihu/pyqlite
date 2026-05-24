from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pyqlite.instruments.swap import SwapType
from pyqlite.time.daycounter import DayCounter
from pyqlite.time.schedule import Schedule


class InflationSwapType(Enum):
    ZERO_COUPON = "ZeroCoupon"
    YEAR_ON_YEAR = "YearOnYear"


@dataclass(frozen=True)
class ZeroCouponInflationSwap:
    swap_type: SwapType
    notional: float
    start_date: object
    maturity_date: object
    fixed_rate: float
    base_index: float
    day_counter: DayCounter


@dataclass(frozen=True)
class YearOnYearInflationSwap:
    swap_type: SwapType
    notional: float
    schedule: Schedule
    fixed_rate: float
    base_index: float
    day_counter: DayCounter
    spread: float = 0.0
