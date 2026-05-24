from __future__ import annotations

from dataclasses import dataclass

from pyquantlib.instruments.fra import PositionType
from pyquantlib.instruments.fx_option import OptionType
from pyquantlib.instruments.swap import SwapType
from pyquantlib.time.schedule import Schedule


@dataclass(frozen=True)
class CommodityForward:
    position: PositionType
    quantity: float
    contract_price: float
    maturity_date: object


@dataclass(frozen=True)
class CommoditySwap:
    swap_type: SwapType
    quantity: float
    fixed_price: float
    schedule: Schedule


@dataclass(frozen=True)
class CommodityOption:
    option_type: OptionType
    quantity: float
    strike: float
    expiry_date: object
