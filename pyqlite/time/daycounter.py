from __future__ import annotations

from datetime import date
from enum import Enum


class DayCounter:
    name = "DayCounter"

    def year_fraction(self, start: date, end: date) -> float:
        raise NotImplementedError


class Actual360(DayCounter):
    name = "Actual/360"

    def year_fraction(self, start: date, end: date) -> float:
        return (end - start).days / 360.0


class Actual365Fixed(DayCounter):
    name = "Actual/365 Fixed"

    def year_fraction(self, start: date, end: date) -> float:
        return (end - start).days / 365.0


class Thirty360Convention(Enum):
    USA = "USA"
    BOND_BASIS = "BondBasis"
    EUROPEAN = "European"
    EUROBOND_BASIS = "EurobondBasis"
    ITALIAN = "Italian"
    GERMAN = "German"
    ISMA = "ISMA"
    ISDA = "ISDA"
    NASD = "NASD"


class Thirty360(DayCounter):
    def __init__(
        self,
        convention: Thirty360Convention = Thirty360Convention.BOND_BASIS,
        termination_date: date | None = None,
    ) -> None:
        self.convention = convention
        self.termination_date = termination_date
        self.name = f"30/360 ({convention.value})"

    def year_fraction(self, start: date, end: date) -> float:
        return self.day_count(start, end) / 360.0

    def day_count(self, start: date, end: date) -> int:
        dd1, dd2 = start.day, end.day
        mm1, mm2 = start.month, end.month
        yy1, yy2 = start.year, end.year
        convention = self.convention
        if convention == Thirty360Convention.USA:
            if _is_last_of_february(start):
                if _is_last_of_february(end):
                    dd2 = 30
                dd1 = 30
            if dd2 == 31 and dd1 >= 30:
                dd2 = 30
            if dd1 == 31:
                dd1 = 30
        elif convention in (Thirty360Convention.BOND_BASIS, Thirty360Convention.ISMA):
            if dd1 == 31:
                dd1 = 30
            if dd2 == 31 and dd1 == 30:
                dd2 = 30
        elif convention in (Thirty360Convention.EUROPEAN, Thirty360Convention.EUROBOND_BASIS):
            if dd1 == 31:
                dd1 = 30
            if dd2 == 31:
                dd2 = 30
        elif convention == Thirty360Convention.ITALIAN:
            if dd1 == 31:
                dd1 = 30
            if dd2 == 31:
                dd2 = 30
            if mm1 == 2 and dd1 > 27:
                dd1 = 30
            if mm2 == 2 and dd2 > 27:
                dd2 = 30
        elif convention in (Thirty360Convention.ISDA, Thirty360Convention.GERMAN):
            if dd1 == 31:
                dd1 = 30
            if dd2 == 31:
                dd2 = 30
            if _is_last_of_february(start):
                dd1 = 30
            if end != self.termination_date and _is_last_of_february(end):
                dd2 = 30
        elif convention == Thirty360Convention.NASD:
            if dd1 == 31:
                dd1 = 30
            if dd2 == 31 and dd1 >= 30:
                dd2 = 30
            if dd2 == 31 and dd1 < 30:
                dd2 = 1
                mm2 += 1
        else:
            raise ValueError(f"unknown 30/360 convention {convention}")
        return 360 * (yy2 - yy1) + 30 * (mm2 - mm1) + (dd2 - dd1)


def _is_last_of_february(d: date) -> bool:
    if d.month != 2:
        return False
    next_day = date.fromordinal(d.toordinal() + 1)
    return next_day.month != 2
