from __future__ import annotations

from dataclasses import dataclass

from pyquantlib.indexes.ibor import IborIndex
from pyquantlib.instruments.swap import SwapType
from pyquantlib.time.daycounter import DayCounter
from pyquantlib.time.schedule import Schedule


@dataclass(frozen=True)
class CrossCurrencyBasisSwap:
    pay_nominal: float
    pay_currency: str
    pay_schedule: Schedule
    pay_index: IborIndex
    pay_spread: float
    pay_gearing: float
    receive_nominal: float
    receive_currency: str
    receive_schedule: Schedule
    receive_index: IborIndex
    receive_spread: float
    receive_gearing: float
    exchange_notionals: bool = True


@dataclass(frozen=True)
class CrossCurrencyFixedFloatSwap:
    swap_type: SwapType
    fixed_nominal: float
    fixed_currency: str
    fixed_schedule: Schedule
    fixed_rate: float
    fixed_day_counter: DayCounter
    float_nominal: float
    float_currency: str
    float_schedule: Schedule
    float_index: IborIndex
    float_spread: float
    exchange_notionals: bool = True
