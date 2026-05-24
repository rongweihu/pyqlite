from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.indexes.ibor import IborIndex
from pyquantlib.time.daycounter import DayCounter


@dataclass(frozen=True)
class CashFlow:
    payment_date: date
    amount: float

    def accrued_amount(self, settlement_date: date) -> float:
        return 0.0


@dataclass(frozen=True)
class FixedRateCoupon:
    payment_date: date
    nominal: float
    rate: float
    day_counter: DayCounter
    accrual_start_date: date
    accrual_end_date: date

    @property
    def accrual_period(self) -> float:
        return self.day_counter.year_fraction(self.accrual_start_date, self.accrual_end_date)

    @property
    def amount(self) -> float:
        return self.nominal * self.rate * self.accrual_period

    def basis_point_value(self) -> float:
        return self.nominal * self.accrual_period * 1.0e-4

    def accrued_amount(self, settlement_date: date) -> float:
        if settlement_date <= self.accrual_start_date or settlement_date > self.accrual_end_date:
            return 0.0
        accrued = self.day_counter.year_fraction(self.accrual_start_date, settlement_date)
        return self.nominal * self.rate * accrued


@dataclass(frozen=True)
class IborCoupon:
    payment_date: date
    nominal: float
    accrual_start_date: date
    accrual_end_date: date
    fixing_date: date
    index: IborIndex
    spread: float = 0.0
    gearing: float = 1.0
    day_counter: DayCounter | None = None

    @property
    def accrual_period(self) -> float:
        dc = self.day_counter or self.index.day_counter
        return dc.year_fraction(self.accrual_start_date, self.accrual_end_date)

    @property
    def rate(self) -> float:
        fixing = self.index.fixing(self.fixing_date, self.accrual_start_date, self.accrual_end_date)
        return self.gearing * fixing + self.spread

    @property
    def amount(self) -> float:
        return self.nominal * self.rate * self.accrual_period

    def basis_point_value(self) -> float:
        return self.nominal * self.accrual_period * 1.0e-4

    def accrued_amount(self, settlement_date: date) -> float:
        if settlement_date <= self.accrual_start_date or settlement_date > self.accrual_end_date:
            return 0.0
        dc = self.day_counter or self.index.day_counter
        accrued = dc.year_fraction(self.accrual_start_date, settlement_date)
        return self.nominal * self.rate * accrued


@dataclass(frozen=True)
class OvernightIndexedCoupon:
    payment_date: date
    nominal: float
    accrual_start_date: date
    accrual_end_date: date
    index: IborIndex
    spread: float = 0.0
    day_counter: DayCounter | None = None

    @property
    def accrual_period(self) -> float:
        dc = self.day_counter or self.index.day_counter
        return dc.year_fraction(self.accrual_start_date, self.accrual_end_date)

    @property
    def rate(self) -> float:
        if self.index.forwarding_curve is None:
            raise ValueError("overnight coupon requires a forwarding curve")
        tau = self.accrual_period
        if tau <= 0.0:
            raise ValueError("invalid overnight accrual period")
        compounded = self.index.forwarding_curve.discount(self.accrual_start_date) / self.index.forwarding_curve.discount(self.accrual_end_date)
        return (compounded - 1.0) / tau + self.spread

    @property
    def amount(self) -> float:
        return self.nominal * self.rate * self.accrual_period

    def basis_point_value(self) -> float:
        return self.nominal * self.accrual_period * 1.0e-4

    def accrued_amount(self, settlement_date: date) -> float:
        if settlement_date <= self.accrual_start_date or settlement_date > self.accrual_end_date:
            return 0.0
        dc = self.day_counter or self.index.day_counter
        accrued = dc.year_fraction(self.accrual_start_date, settlement_date)
        return self.nominal * self.rate * accrued
