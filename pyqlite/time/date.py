from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class TimeUnit(Enum):
    DAYS = "D"
    WEEKS = "W"
    MONTHS = "M"
    YEARS = "Y"


@dataclass(frozen=True)
class Period:
    length: int
    unit: TimeUnit

    @classmethod
    def days(cls, length: int) -> "Period":
        return cls(length, TimeUnit.DAYS)

    @classmethod
    def weeks(cls, length: int) -> "Period":
        return cls(length, TimeUnit.WEEKS)

    @classmethod
    def months(cls, length: int) -> "Period":
        return cls(length, TimeUnit.MONTHS)

    @classmethod
    def years(cls, length: int) -> "Period":
        return cls(length, TimeUnit.YEARS)


def is_end_of_month(d: date) -> bool:
    return add_months(d, 1).replace(day=1).toordinal() - d.toordinal() == 1


def end_of_month(d: date) -> date:
    next_month_start = add_months(d, 1).replace(day=1)
    return date.fromordinal(next_month_start.toordinal() - 1)


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, _month_length(year, month))
    return date(year, month, day)


def advance_date(d: date, period: Period) -> date:
    if period.unit == TimeUnit.DAYS:
        return date.fromordinal(d.toordinal() + period.length)
    if period.unit == TimeUnit.WEEKS:
        return date.fromordinal(d.toordinal() + 7 * period.length)
    if period.unit == TimeUnit.MONTHS:
        return add_months(d, period.length)
    if period.unit == TimeUnit.YEARS:
        return add_months(d, 12 * period.length)
    raise ValueError(f"unsupported period unit: {period.unit}")


def _month_length(year: int, month: int) -> int:
    if month == 12:
        return date(year + 1, 1, 1).toordinal() - date(year, 12, 1).toordinal()
    return date(year, month + 1, 1).toordinal() - date(year, month, 1).toordinal()
