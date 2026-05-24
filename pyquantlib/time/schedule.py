from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from pyquantlib.time.calendar import BusinessDayConvention, Calendar, NullCalendar
from pyquantlib.time.date import Period, advance_date


class DateGenerationRule(Enum):
    FORWARD = "Forward"
    BACKWARD = "Backward"


@dataclass(frozen=True)
class Schedule:
    dates: tuple[date, ...]

    @classmethod
    def generate(
        cls,
        effective_date: date,
        termination_date: date,
        tenor: Period,
        calendar: Calendar | None = None,
        convention: BusinessDayConvention = BusinessDayConvention.MODIFIED_FOLLOWING,
        termination_convention: BusinessDayConvention | None = None,
        rule: DateGenerationRule = DateGenerationRule.FORWARD,
    ) -> "Schedule":
        calendar = calendar or NullCalendar()
        termination_convention = termination_convention or convention
        if effective_date >= termination_date:
            raise ValueError("effective_date must be before termination_date")

        raw = [effective_date]
        if rule == DateGenerationRule.FORWARD:
            cursor = effective_date
            while True:
                cursor = advance_date(cursor, tenor)
                if cursor >= termination_date:
                    break
                raw.append(cursor)
            raw.append(termination_date)
        elif rule == DateGenerationRule.BACKWARD:
            raw = [termination_date]
            cursor = termination_date
            while True:
                cursor = advance_date(cursor, Period(-tenor.length, tenor.unit))
                if cursor <= effective_date:
                    break
                raw.append(cursor)
            raw.append(effective_date)
            raw = list(reversed(raw))
        else:
            raise ValueError(f"unsupported date generation rule: {rule}")

        adjusted = [calendar.adjust(raw[0], convention)]
        adjusted.extend(calendar.adjust(d, convention) for d in raw[1:-1])
        adjusted.append(calendar.adjust(raw[-1], termination_convention))
        deduped = []
        for d in adjusted:
            if not deduped or deduped[-1] != d:
                deduped.append(d)
        return cls(tuple(deduped))

    def __len__(self) -> int:
        return len(self.dates)

    def __iter__(self):
        return iter(self.dates)

    def __getitem__(self, item):
        return self.dates[item]
