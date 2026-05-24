from __future__ import annotations

from dataclasses import dataclass

from pyquantlib.instruments.swap import SwapType
from pyquantlib.time.daycounter import DayCounter
from pyquantlib.time.date import Period
from pyquantlib.time.schedule import Schedule


@dataclass(frozen=True)
class CmsSwap:
    swap_type: SwapType
    nominal: float
    fixed_schedule: Schedule
    fixed_rate: float
    fixed_day_counter: DayCounter
    cms_schedule: Schedule
    cms_tenor: Period
    cms_day_counter: DayCounter
    spread: float = 0.0
    gearing: float = 1.0
