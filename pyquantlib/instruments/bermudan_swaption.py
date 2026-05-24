from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.instruments.swap import VanillaSwap
from pyquantlib.instruments.swaption import SettlementType


@dataclass(frozen=True)
class BermudanSwaption:
    swap: VanillaSwap
    exercise_dates: tuple[date, ...]
    settlement_type: SettlementType = SettlementType.PHYSICAL

    def __post_init__(self) -> None:
        if not self.exercise_dates:
            raise ValueError("Bermudan swaption requires at least one exercise date")
        if tuple(sorted(self.exercise_dates)) != self.exercise_dates:
            raise ValueError("exercise_dates must be sorted")
        if self.exercise_dates[-1] > self.swap.maturity_date:
            raise ValueError("last exercise date must be on or before swap maturity")
