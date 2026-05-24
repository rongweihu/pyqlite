from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from pyquantlib.indexes.ibor import IborIndex


class PositionType(Enum):
    LONG = 1
    SHORT = -1


@dataclass(frozen=True)
class ForwardRateAgreement:
    index: IborIndex
    value_date: date
    maturity_date: date
    position: PositionType
    strike_forward_rate: float
    notional: float
    use_indexed_coupon: bool = False

    @classmethod
    def from_index_maturity(
        cls,
        index: IborIndex,
        value_date: date,
        position: PositionType,
        strike_forward_rate: float,
        notional: float,
    ) -> "ForwardRateAgreement":
        return cls(
            index,
            value_date,
            index.maturity_date(value_date),
            position,
            strike_forward_rate,
            notional,
            use_indexed_coupon=True,
        )

    def __post_init__(self) -> None:
        if self.notional <= 0.0:
            raise ValueError("notional must be positive")
        if self.value_date >= self.maturity_date:
            raise ValueError("value_date must be earlier than maturity_date")

    @property
    def fixing_date(self) -> date:
        return self.index.fixing_date(self.value_date)
