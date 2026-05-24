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
class DigitalFxOption:
    option_type: OptionType
    notional: float
    strike: float
    cash_payoff: float
    expiry_date: date


@dataclass(frozen=True)
class BarrierFxOption:
    option_type: OptionType
    notional: float
    strike: float
    barrier: float
    direction: BarrierDirection
    style: BarrierStyle
    expiry_date: date
    rebate: float = 0.0


@dataclass(frozen=True)
class DoubleBarrierFxOption:
    notional: float
    lower_barrier: float
    upper_barrier: float
    expiry_date: date
    cash_payoff: float
    knock_in: bool = False


@dataclass(frozen=True)
class AsianFxOption:
    option_type: OptionType
    notional: float
    strike: float
    expiry_date: date
    running_accumulator: float = 0.0
    past_fixings: int = 0


@dataclass(frozen=True)
class WindowBarrierFxOption:
    option_type: OptionType
    notional: float
    strike: float
    barrier: float
    direction: BarrierDirection
    style: BarrierStyle
    window_start: date
    window_end: date
    expiry_date: date
    rebate: float = 0.0


@dataclass(frozen=True)
class ForwardStartFxOption:
    option_type: OptionType
    notional: float
    moneyness: float
    reset_date: date
    expiry_date: date


@dataclass(frozen=True)
class QuantoFxOption:
    option_type: OptionType
    notional: float
    strike: float
    expiry_date: date
    quanto_fx_rate: float
    quanto_drift_adjustment: float = 0.0


@dataclass(frozen=True)
class LookbackFxOption:
    option_type: OptionType
    notional: float
    strike: float
    expiry_date: date


@dataclass(frozen=True)
class CliquetFxOption:
    notional: float
    reset_dates: tuple[date, ...]
    local_floor: float
    local_cap: float
    global_floor: float | None = None
    global_cap: float | None = None


@dataclass(frozen=True)
class BasketFxOption:
    option_type: OptionType
    spots: tuple[float, ...]
    foreign_discounts: tuple[float, ...]
    volatilities: tuple[float, ...]
    correlation: tuple[tuple[float, ...], ...]
    weights: tuple[float, ...]
    strike: float
    notional: float
    expiry_date: date
