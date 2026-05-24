from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pyquantlib.market.curves import YieldCurve
from pyquantlib.time.calendar import BusinessDayConvention, Calendar, WeekendsOnly
from pyquantlib.time.date import Period
from pyquantlib.time.daycounter import Actual360, DayCounter


@dataclass
class IborIndex:
    name: str
    tenor: Period
    settlement_days: int
    calendar: Calendar = field(default_factory=WeekendsOnly)
    day_counter: DayCounter = field(default_factory=Actual360)
    forwarding_curve: YieldCurve | None = None
    fixings: dict[date, float] = field(default_factory=dict)
    convention: BusinessDayConvention = BusinessDayConvention.MODIFIED_FOLLOWING
    end_of_month: bool = False

    def fixing_date(self, value_date: date) -> date:
        return self.calendar.advance(value_date, -self.settlement_days, BusinessDayConvention.PRECEDING)

    def value_date(self, fixing_date: date) -> date:
        return self.calendar.advance(fixing_date, self.settlement_days)

    def maturity_date(self, value_date: date) -> date:
        return self.calendar.advance(value_date, self.tenor, self.convention, self.end_of_month)

    def add_fixing(self, fixing_date: date, fixing: float) -> None:
        self.fixings[fixing_date] = fixing

    def fixing(self, fixing_date: date, value_date: date | None = None, maturity_date: date | None = None) -> float:
        if fixing_date in self.fixings:
            return self.fixings[fixing_date]
        if self.forwarding_curve is None:
            raise ValueError(f"missing fixing for {fixing_date} and no forwarding curve is set")
        value_date = value_date or self.value_date(fixing_date)
        maturity_date = maturity_date or self.maturity_date(value_date)
        tau = self.day_counter.year_fraction(value_date, maturity_date)
        if tau <= 0.0:
            raise ValueError("invalid ibor accrual period")
        return (self.forwarding_curve.discount(value_date) / self.forwarding_curve.discount(maturity_date) - 1.0) / tau
