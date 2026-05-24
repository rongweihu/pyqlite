from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from pyqlite.instruments.swap import VanillaSwap


class SettlementType(Enum):
    PHYSICAL = "Physical"


@dataclass(frozen=True)
class Swaption:
    swap: VanillaSwap
    exercise_date: date
    settlement_type: SettlementType = SettlementType.PHYSICAL

    def __post_init__(self) -> None:
        if self.exercise_date > self.swap.start_date:
            raise ValueError("exercise_date must be on or before the swap start date")
