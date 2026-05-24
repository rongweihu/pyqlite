from __future__ import annotations

from dataclasses import dataclass

from pyqlite.instruments.fra import PositionType
from pyqlite.instruments.fx_option import OptionType
from pyqlite.instruments.swap import SwapType
from pyqlite.time.schedule import Schedule


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
