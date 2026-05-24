from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class OptionType(Enum):
    CALL = 1
    PUT = -1


@dataclass(frozen=True)
class FxOption:
    option_type: OptionType
    domestic_currency: str
    foreign_currency: str
    foreign_notional: float
    strike: float
    expiry_date: date

    def __post_init__(self) -> None:
        if not self.domestic_currency:
            raise ValueError("domestic currency must not be empty")
        if not self.foreign_currency:
            raise ValueError("foreign currency must not be empty")
        if self.domestic_currency == self.foreign_currency:
            raise ValueError("domestic and foreign currencies must be different")
        if self.foreign_notional <= 0.0:
            raise ValueError("foreign notional must be positive")
        if self.strike <= 0.0:
            raise ValueError("strike must be positive")

    @property
    def sign(self) -> int:
        return self.option_type.value
