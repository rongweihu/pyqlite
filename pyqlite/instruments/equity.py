from __future__ import annotations

from dataclasses import dataclass

from pyqlite.instruments.fx_option import OptionType
from pyqlite.instruments.swap import SwapType
from pyqlite.time.daycounter import DayCounter
from pyqlite.time.schedule import Schedule


@dataclass(frozen=True)
class EquityOption:
    option_type: OptionType
    quantity: float
    strike: float
    expiry_date: object


@dataclass(frozen=True)
class EquityTotalReturnSwap:
    swap_type: SwapType
    notional: float
    initial_price: float
    maturity_date: object
    funding_schedule: Schedule
    funding_spread: float
    funding_day_counter: DayCounter
    funding_gearing: float = 1.0
