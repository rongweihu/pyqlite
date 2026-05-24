from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from pyquantlib.instruments.fx_option import OptionType


class BarrierDirection(Enum):
    UP = "Up"
    DOWN = "Down"


class BarrierStyle(Enum):
    KNOCK_IN = "KnockIn"
    KNOCK_OUT = "KnockOut"


@dataclass(frozen=True)
class EquityBarrierOption:
    option_type: OptionType
    quantity: float
    strike: float
    barrier: float
    direction: BarrierDirection
    style: BarrierStyle
    expiry_date: date
    rebate: float = 0.0


@dataclass(frozen=True)
class EquityAsianOption:
    option_type: OptionType
    quantity: float
    strike: float
    expiry_date: date
    fixing_dates: tuple[date, ...] = ()


@dataclass(frozen=True)
class EquityLookbackOption:
    option_type: OptionType
    quantity: float
    strike: float
    expiry_date: date


@dataclass(frozen=True)
class EquityCliquetOption:
    quantity: float
    reset_dates: tuple[date, ...]
    local_floor: float
    local_cap: float
    global_floor: float | None = None
    global_cap: float | None = None


@dataclass(frozen=True)
class EquityForwardStartOption:
    option_type: OptionType
    quantity: float
    moneyness: float
    start_date: date
    expiry_date: date


@dataclass(frozen=True)
class EquityBasketOption:
    option_type: OptionType
    quantities: tuple[float, ...]
    spots: tuple[float, ...]
    strike: float
    expiry_date: date
    correlation: tuple[tuple[float, ...], ...]
