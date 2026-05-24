from __future__ import annotations

from datetime import date, timedelta
from enum import Enum

from pyquantlib.time.date import (
    Period,
    TimeUnit,
    advance_date,
    end_of_month as date_end_of_month,
    is_end_of_month as date_is_end_of_month,
)


class BusinessDayConvention(Enum):
    FOLLOWING = "Following"
    MODIFIED_FOLLOWING = "ModifiedFollowing"
    PRECEDING = "Preceding"
    MODIFIED_PRECEDING = "ModifiedPreceding"
    UNADJUSTED = "Unadjusted"


class Calendar:
    def is_business_day(self, d: date) -> bool:
        return True

    def adjust(
        self,
        d: date,
        convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
    ) -> date:
        if convention == BusinessDayConvention.UNADJUSTED or self.is_business_day(d):
            return d
        if convention in (BusinessDayConvention.FOLLOWING, BusinessDayConvention.MODIFIED_FOLLOWING):
            adjusted = d
            while not self.is_business_day(adjusted):
                adjusted += timedelta(days=1)
            if convention == BusinessDayConvention.MODIFIED_FOLLOWING and adjusted.month != d.month:
                return self.adjust(d, BusinessDayConvention.PRECEDING)
            return adjusted
        if convention in (BusinessDayConvention.PRECEDING, BusinessDayConvention.MODIFIED_PRECEDING):
            adjusted = d
            while not self.is_business_day(adjusted):
                adjusted -= timedelta(days=1)
            if convention == BusinessDayConvention.MODIFIED_PRECEDING and adjusted.month != d.month:
                return self.adjust(d, BusinessDayConvention.FOLLOWING)
            return adjusted
        raise ValueError(f"unsupported business-day convention: {convention}")

    def advance(
        self,
        d: date,
        business_days: int | Period,
        convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING,
        end_of_month_flag: bool = False,
    ) -> date:
        if isinstance(business_days, Period):
            if business_days.unit == TimeUnit.DAYS:
                return self.advance(d, business_days.length, convention, end_of_month_flag)
            advanced = advance_date(d, business_days)
            if business_days.unit in (TimeUnit.MONTHS, TimeUnit.YEARS) and end_of_month_flag:
                if convention == BusinessDayConvention.UNADJUSTED:
                    if date_is_end_of_month(d):
                        return date_end_of_month(advanced)
                elif self.is_end_of_month(d):
                    return self.end_of_month(advanced)
            return self.adjust(advanced, convention)
        if business_days == 0:
            return self.adjust(d, convention)
        step = 1 if business_days > 0 else -1
        remaining = abs(business_days)
        result = d
        while remaining:
            result += timedelta(days=step)
            if self.is_business_day(result):
                remaining -= 1
        return result

    def is_end_of_month(self, d: date) -> bool:
        return d >= self.end_of_month(d)

    def end_of_month(self, d: date) -> date:
        return self.adjust(date_end_of_month(d), BusinessDayConvention.PRECEDING)


class NullCalendar(Calendar):
    pass


class WeekendsOnly(Calendar):
    def is_business_day(self, d: date) -> bool:
        return d.weekday() < 5
