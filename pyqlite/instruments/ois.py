from __future__ import annotations

from dataclasses import dataclass

from pyqlite.cashflows.legs import fixed_rate_leg, overnight_leg
from pyqlite.indexes.ibor import IborIndex
from pyqlite.instruments.swap import SwapType
from pyqlite.time.calendar import BusinessDayConvention, Calendar
from pyqlite.time.daycounter import DayCounter
from pyqlite.time.schedule import Schedule


@dataclass(frozen=True)
class OvernightIndexedSwap:
    swap_type: SwapType
    fixed_nominals: tuple[float, ...]
    fixed_schedule: Schedule
    fixed_rate: float
    fixed_day_counter: DayCounter
    overnight_nominals: tuple[float, ...]
    overnight_schedule: Schedule
    overnight_index: IborIndex
    spread: float = 0.0
    payment_lag: int = 0
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING
    payment_calendar: Calendar | None = None

    @classmethod
    def from_nominal(
        cls,
        swap_type: SwapType,
        nominal: float,
        schedule: Schedule,
        fixed_rate: float,
        fixed_day_counter: DayCounter,
        overnight_index: IborIndex,
        spread: float = 0.0,
    ) -> "OvernightIndexedSwap":
        periods = len(schedule.dates) - 1
        return cls(
            swap_type,
            (nominal,) * periods,
            schedule,
            fixed_rate,
            fixed_day_counter,
            (nominal,) * periods,
            schedule,
            overnight_index,
            spread,
        )

    @property
    def fixed_leg(self) -> list:
        return fixed_rate_leg(
            self.fixed_schedule,
            self.fixed_nominals,
            self.fixed_rate,
            self.fixed_day_counter,
            payment_calendar=self.payment_calendar,
            payment_convention=self.payment_convention,
        )

    @property
    def overnight_leg(self) -> list:
        return overnight_leg(
            self.overnight_schedule,
            self.overnight_nominals,
            self.overnight_index,
            self.spread,
            payment_calendar=self.payment_calendar,
            payment_convention=self.payment_convention,
            payment_lag=self.payment_lag,
        )

    @property
    def legs(self) -> list[list]:
        return [self.fixed_leg, self.overnight_leg]

    @property
    def payer_signs(self) -> list[float]:
        if self.swap_type == SwapType.PAYER:
            return [-1.0, 1.0]
        return [1.0, -1.0]

    @property
    def fixed_leg_bps(self) -> float:
        return sum(cf.basis_point_value() for cf in self.fixed_leg)
