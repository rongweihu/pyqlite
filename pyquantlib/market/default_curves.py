from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from pyquantlib.time.daycounter import Actual365Fixed, DayCounter


class DefaultProbabilityCurve:
    reference_date: date
    day_counter: DayCounter

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def survival_probability(self, d: date) -> float:
        return self.survival_probability_time(max(self.time_from_reference(d), 0.0))

    def default_probability(self, start: date, end: date) -> float:
        return max(0.0, self.survival_probability(start) - self.survival_probability(end))

    def survival_probability_time(self, t: float) -> float:
        raise NotImplementedError


@dataclass(frozen=True)
class FlatHazardRate(DefaultProbabilityCurve):
    reference_date: date
    hazard_rate: float
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if self.hazard_rate < 0.0:
            raise ValueError("hazard_rate must be non-negative")

    def survival_probability_time(self, t: float) -> float:
        return math.exp(-self.hazard_rate * max(t, 0.0))


@dataclass(frozen=True)
class SurvivalProbabilityCurve(DefaultProbabilityCurve):
    reference_date: date
    dates: tuple[date, ...]
    survival_probabilities: tuple[float, ...]
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.survival_probabilities):
            raise ValueError("dates and survival probabilities must have the same length")
        if not self.dates:
            raise ValueError("at least one survival probability node is required")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("survival probability dates must be sorted")
        if self.dates[0] <= self.reference_date:
            raise ValueError("survival probability dates must be after reference date")
        if any(p <= 0.0 or p > 1.0 for p in self.survival_probabilities):
            raise ValueError("survival probabilities must be in (0, 1]")

    def survival_probability_time(self, t: float) -> float:
        if t <= 0.0:
            return 1.0
        times = tuple(self.time_from_reference(d) for d in self.dates)
        log_survivals = tuple(math.log(p) for p in self.survival_probabilities)
        if t <= times[0]:
            return math.exp(_linear(0.0, 0.0, times[0], log_survivals[0], t))
        if t >= times[-1]:
            if len(times) == 1:
                return math.exp(_linear(0.0, 0.0, times[0], log_survivals[0], t))
            return math.exp(_linear(times[-2], log_survivals[-2], times[-1], log_survivals[-1], t))
        for i in range(1, len(times)):
            if t <= times[i]:
                return math.exp(_linear(times[i - 1], log_survivals[i - 1], times[i], log_survivals[i], t))
        raise RuntimeError("unreachable survival interpolation state")


def _linear(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 == x0:
        return y1
    return y0 + (x - x0) / (x1 - x0) * (y1 - y0)
