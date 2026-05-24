from __future__ import annotations

from collections.abc import Sequence

from pyqlite.cashflows.cashflow import FixedRateCoupon, IborCoupon, OvernightIndexedCoupon
from pyqlite.indexes.ibor import IborIndex
from pyqlite.time.calendar import BusinessDayConvention, Calendar, NullCalendar
from pyqlite.time.daycounter import DayCounter
from pyqlite.time.schedule import Schedule


def fixed_rate_leg(
    schedule: Schedule,
    nominal: float | Sequence[float],
    rate: float | Sequence[float],
    day_counter: DayCounter,
    payment_calendar: Calendar | None = None,
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
) -> list[FixedRateCoupon]:
    payment_calendar = payment_calendar or NullCalendar()
    coupons = []
    periods = len(schedule.dates) - 1
    notionals = _expand(nominal, periods, "nominal")
    rates = _expand(rate, periods, "rate")
    for i, (start, end) in enumerate(zip(schedule.dates[:-1], schedule.dates[1:])):
        coupons.append(
            FixedRateCoupon(
                payment_date=payment_calendar.adjust(end, payment_convention),
                nominal=notionals[i],
                rate=rates[i],
                day_counter=day_counter,
                accrual_start_date=start,
                accrual_end_date=end,
            )
        )
    return coupons


def ibor_leg(
    schedule: Schedule,
    nominal: float | Sequence[float],
    index: IborIndex,
    spread: float | Sequence[float] = 0.0,
    day_counter: DayCounter | None = None,
    payment_calendar: Calendar | None = None,
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
    gearing: float | Sequence[float] = 1.0,
) -> list[IborCoupon]:
    payment_calendar = payment_calendar or index.calendar
    coupons = []
    periods = len(schedule.dates) - 1
    notionals = _expand(nominal, periods, "nominal")
    spreads = _expand(spread, periods, "spread")
    gearings = _expand(gearing, periods, "gearing")
    for i, (start, end) in enumerate(zip(schedule.dates[:-1], schedule.dates[1:])):
        coupons.append(
            IborCoupon(
                payment_date=payment_calendar.adjust(end, payment_convention),
                nominal=notionals[i],
                accrual_start_date=start,
                accrual_end_date=end,
                fixing_date=index.fixing_date(start),
                index=index,
                spread=spreads[i],
                gearing=gearings[i],
                day_counter=day_counter,
            )
        )
    return coupons


def overnight_leg(
    schedule: Schedule,
    nominal: float | Sequence[float],
    index: IborIndex,
    spread: float | Sequence[float] = 0.0,
    day_counter: DayCounter | None = None,
    payment_calendar: Calendar | None = None,
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
    payment_lag: int = 0,
) -> list[OvernightIndexedCoupon]:
    payment_calendar = payment_calendar or index.calendar
    periods = len(schedule.dates) - 1
    notionals = _expand(nominal, periods, "nominal")
    spreads = _expand(spread, periods, "spread")
    coupons = []
    for i, (start, end) in enumerate(zip(schedule.dates[:-1], schedule.dates[1:])):
        payment_date = payment_calendar.adjust(end, payment_convention)
        if payment_lag:
            payment_date = payment_calendar.advance(payment_date, payment_lag)
        coupons.append(
            OvernightIndexedCoupon(
                payment_date=payment_date,
                nominal=notionals[i],
                accrual_start_date=start,
                accrual_end_date=end,
                index=index,
                spread=spreads[i],
                day_counter=day_counter,
            )
        )
    return coupons


def _expand(value: float | Sequence[float], length: int, name: str) -> tuple[float, ...]:
    if isinstance(value, (int, float)):
        return (float(value),) * length
    result = tuple(float(x) for x in value)
    if len(result) != length:
        raise ValueError(f"{name} size ({len(result)}) must match number of periods ({length})")
    return result
