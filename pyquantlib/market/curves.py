from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from pyquantlib.time.daycounter import Actual365Fixed, DayCounter


class YieldCurve:
    reference_date: date
    day_counter: DayCounter

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def discount(self, d: date) -> float:
        return self.discount_time(self.time_from_reference(d))

    def discount_time(self, t: float) -> float:
        raise NotImplementedError

    def zero_rate(self, d: date) -> float:
        return self.zero_rate_time(self.time_from_reference(d))

    def zero_rate_time(self, t: float) -> float:
        if t <= 0.0:
            return 0.0
        return -math.log(self.discount_time(t)) / t

    def forward_rate(self, start: date, end: date) -> float:
        tau = self.day_counter.year_fraction(start, end)
        if tau <= 0.0:
            raise ValueError("forward period must be positive")
        return (self.discount(start) / self.discount(end) - 1.0) / tau

    def nodes(self) -> list[tuple[date, float]]:
        raise NotImplementedError


@dataclass(frozen=True)
class FlatForwardCurve(YieldCurve):
    reference_date: date
    rate: float
    day_counter: DayCounter = Actual365Fixed()

    def discount_time(self, t: float) -> float:
        return math.exp(-self.rate * t)

    def nodes(self) -> list[tuple[date, float]]:
        return [(self.reference_date, self.rate)]


@dataclass(frozen=True)
class DiscountCurve(YieldCurve):
    reference_date: date
    dates: tuple[date, ...]
    discounts: tuple[float, ...]
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.discounts):
            raise ValueError("dates and discounts must have the same length")
        if not self.dates:
            raise ValueError("at least one curve point is required")
        if any(df <= 0.0 for df in self.discounts):
            raise ValueError("discount factors must be positive")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("dates must be sorted")
        if self.dates[0] <= self.reference_date:
            raise ValueError("discount curve pillar dates must be after the reference date")

    def discount_time(self, t: float) -> float:
        if t <= 0.0:
            return 1.0
        times = [self.time_from_reference(x) for x in self.dates]
        log_dfs = [math.log(x) for x in self.discounts]
        if t <= times[0]:
            return math.exp(_linear(0.0, 0.0, times[0], log_dfs[0], t))
        if t >= times[-1]:
            if len(times) == 1:
                return math.exp(_linear(0.0, 0.0, times[0], log_dfs[0], t))
            return math.exp(_linear(times[-2], log_dfs[-2], times[-1], log_dfs[-1], t))
        for i in range(1, len(times)):
            if t <= times[i]:
                return math.exp(_linear(times[i - 1], log_dfs[i - 1], times[i], log_dfs[i], t))
        raise RuntimeError("unreachable interpolation state")

    def nodes(self) -> list[tuple[date, float]]:
        return list(zip(self.dates, self.discounts))


@dataclass(frozen=True)
class ZeroCurve(YieldCurve):
    """Dated zero-rate curve with linear interpolation on continuous zero rates.

    This mirrors QuantLib's practical distinction between discount curves and
    zero curves: discount curves interpolate log discount factors, while zero
    curves interpolate zero yields and derive discounts from them.
    """

    reference_date: date
    dates: tuple[date, ...]
    zero_rates: tuple[float, ...]
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.zero_rates):
            raise ValueError("dates and zero_rates must have the same length")
        if not self.dates:
            raise ValueError("at least one curve point is required")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("dates must be sorted")
        if self.dates[0] <= self.reference_date:
            raise ValueError("zero curve pillar dates must be after the reference date")

    def discount_time(self, t: float) -> float:
        if t <= 0.0:
            return 1.0
        zero = self.zero_rate_time(t)
        return math.exp(-zero * t)

    def zero_rate_time(self, t: float) -> float:
        if t <= 0.0:
            return 0.0
        times = [self.time_from_reference(x) for x in self.dates]
        if t <= times[0]:
            return self.zero_rates[0]
        if t >= times[-1]:
            if len(times) == 1:
                return self.zero_rates[-1]
            slope = (self.zero_rates[-1] - self.zero_rates[-2]) / (times[-1] - times[-2])
            inst_fwd_max = self.zero_rates[-1] + times[-1] * slope
            return (self.zero_rates[-1] * times[-1] + inst_fwd_max * (t - times[-1])) / t
        for i in range(1, len(times)):
            if t <= times[i]:
                return _linear(times[i - 1], self.zero_rates[i - 1], times[i], self.zero_rates[i], t)
        raise RuntimeError("unreachable interpolation state")

    def nodes(self) -> list[tuple[date, float]]:
        return list(zip(self.dates, self.zero_rates))


def _linear(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 == x0:
        return y1
    weight = (x - x0) / (x1 - x0)
    return y0 + weight * (y1 - y0)
