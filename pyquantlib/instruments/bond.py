from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.cashflows.cashflow import CashFlow, FixedRateCoupon
from pyquantlib.time.calendar import BusinessDayConvention, Calendar, NullCalendar
from pyquantlib.time.daycounter import DayCounter
from pyquantlib.time.schedule import Schedule


@dataclass(frozen=True)
class Bond:
    settlement_days: int
    calendar: Calendar
    issue_date: date | None
    maturity_date: date
    cashflows: tuple[CashFlow | FixedRateCoupon, ...]
    face_amount: float = 100.0

    def __post_init__(self) -> None:
        if self.settlement_days < 0:
            raise ValueError("settlement_days must be non-negative")
        if self.face_amount <= 0.0:
            raise ValueError("face_amount must be positive")
        if not self.cashflows:
            raise ValueError("bond with no cashflows")

    def settlement_date(self, evaluation_date: date) -> date:
        return self.calendar.advance(evaluation_date, self.settlement_days)


@dataclass(frozen=True)
class FixedRateBond(Bond):
    @classmethod
    def from_schedule(
        cls,
        settlement_days: int,
        face_amount: float,
        schedule: Schedule,
        coupon_rate: float,
        day_counter: DayCounter,
        payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
        redemption: float = 100.0,
        issue_date: date | None = None,
        payment_calendar: Calendar | None = None,
    ) -> "FixedRateBond":
        payment_calendar = payment_calendar or NullCalendar()
        coupons: list[CashFlow | FixedRateCoupon] = []
        for start, end in zip(schedule.dates[:-1], schedule.dates[1:]):
            coupons.append(
                FixedRateCoupon(
                    payment_date=payment_calendar.adjust(end, payment_convention),
                    nominal=face_amount,
                    rate=coupon_rate,
                    day_counter=day_counter,
                    accrual_start_date=start,
                    accrual_end_date=end,
                )
            )
        coupons.append(CashFlow(payment_calendar.adjust(schedule.dates[-1], payment_convention), face_amount * redemption / 100.0))
        return cls(
            settlement_days,
            payment_calendar,
            issue_date,
            schedule.dates[-1],
            tuple(coupons),
            face_amount,
        )


@dataclass(frozen=True)
class ZeroCouponBond(Bond):
    @classmethod
    def from_maturity(
        cls,
        settlement_days: int,
        calendar: Calendar,
        face_amount: float,
        maturity_date: date,
        redemption: float = 100.0,
        issue_date: date | None = None,
        payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
    ) -> "ZeroCouponBond":
        payment_date = calendar.adjust(maturity_date, payment_convention)
        return cls(
            settlement_days,
            calendar,
            issue_date,
            maturity_date,
            (CashFlow(payment_date, face_amount * redemption / 100.0),),
            face_amount,
        )
