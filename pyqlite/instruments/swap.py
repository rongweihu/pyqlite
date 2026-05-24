from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from pyqlite.cashflows.legs import fixed_rate_leg, ibor_leg
from pyqlite.indexes.ibor import IborIndex
from pyqlite.time.calendar import BusinessDayConvention
from pyqlite.time.daycounter import DayCounter
from pyqlite.time.schedule import Schedule


class SwapType(Enum):
    RECEIVER = -1
    PAYER = 1


@dataclass(frozen=True)
class VanillaSwap:
    swap_type: SwapType
    nominal: float
    fixed_schedule: Schedule
    fixed_rate: float
    fixed_day_counter: DayCounter
    floating_schedule: Schedule
    ibor_index: IborIndex
    spread: float
    floating_day_counter: DayCounter
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING

    def __post_init__(self) -> None:
        if self.nominal <= 0.0:
            raise ValueError("nominal must be positive")
        if len(self.fixed_schedule) < 2:
            raise ValueError("fixed schedule must contain at least two dates")
        if len(self.floating_schedule) < 2:
            raise ValueError("floating schedule must contain at least two dates")

    @property
    def fixed_leg(self) -> list:
        return fixed_rate_leg(
            self.fixed_schedule,
            self.nominal,
            self.fixed_rate,
            self.fixed_day_counter,
            payment_convention=self.payment_convention,
        )

    @property
    def floating_leg(self) -> list:
        return ibor_leg(
            self.floating_schedule,
            self.nominal,
            self.ibor_index,
            self.spread,
            self.floating_day_counter,
            payment_convention=self.payment_convention,
        )

    @property
    def legs(self) -> list[list]:
        return [self.fixed_leg, self.floating_leg]

    @property
    def payer_signs(self) -> list[float]:
        if self.swap_type == SwapType.PAYER:
            return [-1.0, 1.0]
        return [1.0, -1.0]

    @property
    def start_date(self) -> date:
        return min(self.fixed_schedule[0], self.floating_schedule[0])

    @property
    def maturity_date(self) -> date:
        return max(self.fixed_schedule[-1], self.floating_schedule[-1])
