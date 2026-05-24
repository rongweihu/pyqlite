from __future__ import annotations

from dataclasses import dataclass

from pyqlite.instruments.fra import PositionType


@dataclass(frozen=True)
class VarianceSwap:
    position: PositionType
    strike: float
    notional: float
    start_date: object
    maturity_date: object


@dataclass(frozen=True)
class VolatilitySwap:
    position: PositionType
    strike: float
    notional: float
    start_date: object
    maturity_date: object
