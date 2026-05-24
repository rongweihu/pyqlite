from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.time.daycounter import Actual365Fixed, DayCounter
from pyquantlib.market.curves import YieldCurve
from pyquantlib.math.black_delta import AtmType, BlackDeltaCalculator, DeltaType


@dataclass(frozen=True)
class BlackConstantVol:
    reference_date: date
    volatility: float
    day_counter: DayCounter = Actual365Fixed()

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def black_variance(self, d: date, strike: float | None = None) -> float:
        return self.black_variance_time(max(self.time_from_reference(d), 0.0), strike)

    def black_variance_time(self, t: float, strike: float | None = None) -> float:
        return self.volatility * self.volatility * t

    def black_vol(self, d: date, strike: float | None = None) -> float:
        return self.volatility

    def black_vol_time(self, t: float, strike: float | None = None) -> float:
        return self.volatility


@dataclass(frozen=True)
class BlackVarianceCurve:
    """ATM volatility term structure interpolated on total variance."""

    reference_date: date
    dates: tuple[date, ...]
    volatilities: tuple[float, ...]
    day_counter: DayCounter = Actual365Fixed()
    force_monotone_variance: bool = True

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.volatilities):
            raise ValueError("dates and volatilities must have the same length")
        if not self.dates:
            raise ValueError("at least one volatility pillar is required")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("volatility dates must be sorted")
        if self.dates[0] <= self.reference_date:
            raise ValueError("volatility dates must be after the reference date")
        if any(vol < 0.0 for vol in self.volatilities):
            raise ValueError("volatilities must be non-negative")
        times = [self.time_from_reference(x) for x in self.dates]
        variances = [vol * vol * time for vol, time in zip(self.volatilities, times)]
        if self.force_monotone_variance and any(curr < prev for prev, curr in zip(variances, variances[1:])):
            raise ValueError("variance must be non-decreasing")

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def black_variance(self, d: date, strike: float | None = None) -> float:
        return self.black_variance_time(max(self.time_from_reference(d), 0.0), strike)

    def black_variance_time(self, t: float, strike: float | None = None) -> float:
        if t == 0.0:
            return 0.0
        times = [self.time_from_reference(x) for x in self.dates]
        variances = [vol * vol * max(time, 0.0) for vol, time in zip(self.volatilities, times)]
        if t <= times[0]:
            return variances[0] * t / times[0]
        if t >= times[-1]:
            vol = self.volatilities[-1]
            return vol * vol * t
        for i in range(1, len(times)):
            if t <= times[i]:
                return _linear(times[i - 1], variances[i - 1], times[i], variances[i], t)
        raise RuntimeError("unreachable variance interpolation state")

    def black_vol(self, d: date, strike: float | None = None) -> float:
        return self.black_vol_time(max(self.time_from_reference(d), 0.0), strike)

    def black_vol_time(self, t: float, strike: float | None = None) -> float:
        if t == 0.0:
            return self.volatilities[0]
        return (self.black_variance_time(t, strike) / t) ** 0.5


@dataclass(frozen=True)
class BlackVarianceSurface:
    """Expiry/strike Black volatility surface interpolated on total variance."""

    reference_date: date
    dates: tuple[date, ...]
    strikes: tuple[float, ...]
    volatilities: tuple[tuple[float, ...], ...]
    day_counter: DayCounter = Actual365Fixed()

    def __post_init__(self) -> None:
        if not self.dates or not self.strikes:
            raise ValueError("surface requires at least one date and one strike")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("surface dates must be sorted")
        if self.dates[0] <= self.reference_date:
            raise ValueError("surface dates must be after the reference date")
        if tuple(sorted(self.strikes)) != self.strikes:
            raise ValueError("surface strikes must be sorted")
        if len(self.volatilities) != len(self.dates):
            raise ValueError("volatility rows must match dates")
        for row in self.volatilities:
            if len(row) != len(self.strikes):
                raise ValueError("each volatility row must match strikes")
            if any(vol < 0.0 for vol in row):
                raise ValueError("volatilities must be non-negative")

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def black_variance(self, d: date, strike: float | None = None) -> float:
        return self.black_variance_time(max(self.time_from_reference(d), 0.0), strike)

    def black_variance_time(self, t: float, strike: float | None = None) -> float:
        if t == 0.0:
            return 0.0
        k = strike if strike is not None else self.strikes[len(self.strikes) // 2]
        times = [self.time_from_reference(x) for x in self.dates]
        variance_rows = [
            [vol * vol * max(time, 0.0) for vol in row]
            for row, time in zip(self.volatilities, times)
        ]
        if t <= times[0]:
            row_var = _interp_strike(self.strikes, variance_rows[0], k)
            return row_var * t / times[0]
        if t >= times[-1]:
            vol = _interp_strike(self.strikes, self.volatilities[-1], k)
            return vol * vol * t
        for i in range(1, len(times)):
            if t <= times[i]:
                lower = _interp_strike(self.strikes, variance_rows[i - 1], k)
                upper = _interp_strike(self.strikes, variance_rows[i], k)
                return _linear(times[i - 1], lower, times[i], upper, t)
        raise RuntimeError("unreachable variance interpolation state")

    def black_vol(self, d: date, strike: float | None = None) -> float:
        return self.black_vol_time(max(self.time_from_reference(d), 0.0), strike)

    def black_vol_time(self, t: float, strike: float | None = None) -> float:
        if t == 0.0:
            return _interp_strike(self.strikes, self.volatilities[0], strike or self.strikes[0])
        return (self.black_variance_time(t, strike) / t) ** 0.5


def _interp_strike(
    strikes: tuple[float, ...],
    values: list[float] | tuple[float, ...],
    strike: float,
    flat_extrapolation: bool = False,
) -> float:
    if len(strikes) == 1:
        return values[0]
    if strike <= strikes[0]:
        if flat_extrapolation:
            return values[0]
        return _linear(strikes[0], values[0], strikes[1], values[1], strike)
    if strike >= strikes[-1]:
        if flat_extrapolation:
            return values[-1]
        return _linear(strikes[-2], values[-2], strikes[-1], values[-1], strike)
    for i in range(1, len(strikes)):
        if strike <= strikes[i]:
            return _linear(strikes[i - 1], values[i - 1], strikes[i], values[i], strike)
    raise RuntimeError("unreachable strike interpolation state")


def _linear(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 == x0:
        return y1
    weight = (x - x0) / (x1 - x0)
    return y0 + weight * (y1 - y0)


@dataclass(frozen=True)
class BlackDeltaVolSurface:
    """FX Black volatility surface parameterized by market deltas and expiries.

    This is the Python analogue of QuantLib's BlackVolatilitySurfaceDelta for
    the conventions currently supported by pyquantlib. Market data columns are
    put deltas, optional ATM, then call deltas.
    """

    reference_date: date
    dates: tuple[date, ...]
    put_deltas: tuple[float, ...]
    call_deltas: tuple[float, ...]
    has_atm: bool
    volatilities: tuple[tuple[float, ...], ...]
    spot: float
    domestic_curve: YieldCurve
    foreign_curve: YieldCurve
    day_counter: DayCounter = Actual365Fixed()
    delta_type: DeltaType = DeltaType.SPOT
    atm_type: AtmType = AtmType.ATM_DELTA_NEUTRAL
    flat_strike_extrapolation: bool = False

    def __post_init__(self) -> None:
        if not self.dates:
            raise ValueError("delta surface requires at least one expiry")
        if tuple(sorted(self.dates)) != self.dates:
            raise ValueError("surface dates must be sorted")
        if self.dates[0] <= self.reference_date:
            raise ValueError("surface dates must be after the reference date")
        columns = len(self.put_deltas) + (1 if self.has_atm else 0) + len(self.call_deltas)
        if columns == 0:
            raise ValueError("delta surface requires at least one delta or ATM column")
        if len(self.volatilities) != len(self.dates):
            raise ValueError("volatility rows must match dates")
        for row in self.volatilities:
            if len(row) != columns:
                raise ValueError("volatility columns must match put deltas + ATM + call deltas")
            if any(vol < 0.0 for vol in row):
                raise ValueError("volatilities must be non-negative")
        for delta in self.put_deltas:
            if delta >= 0.0:
                raise ValueError("put deltas must be negative")
        for delta in self.call_deltas:
            if delta <= 0.0:
                raise ValueError("call deltas must be positive")
        if self.spot <= 0.0:
            raise ValueError("spot must be positive")

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def black_variance(self, d: date, strike: float | None = None) -> float:
        return self.black_variance_time(max(self.time_from_reference(d), 0.0), strike)

    def black_variance_time(self, t: float, strike: float | None = None) -> float:
        if t == 0.0:
            return 0.0
        vol = self.black_vol_time(t, strike)
        return vol * vol * t

    def black_vol(self, d: date, strike: float | None = None) -> float:
        return self.black_vol_time(max(self.time_from_reference(d), 0.0), strike)

    def black_vol_time(self, t: float, strike: float | None = None) -> float:
        if t == 0.0:
            return self._atm_or_middle_vol(t)
        if strike is None or strike == 0.0:
            if self.has_atm:
                return self._column_vol(len(self.put_deltas), t)
            strike = self.atm_level(t)
        strikes, vols = self._smile(t)
        return _interp_strike(tuple(strikes), tuple(vols), strike, self.flat_strike_extrapolation)

    def atm_level(self, t: float) -> float:
        return self.spot * self.foreign_curve.discount_time(t) / self.domestic_curve.discount_time(t)

    def _smile(self, t: float) -> tuple[list[float], list[float]]:
        d_discount = self.domestic_curve.discount_time(t)
        f_discount = self.foreign_curve.discount_time(t)
        sqrt_t = t ** 0.5
        points: dict[float, float] = {}
        col = 0
        for delta in self.put_deltas:
            vol = self._column_vol(col, t)
            strike = BlackDeltaCalculator(
                -1,
                self.delta_type,
                self.spot,
                d_discount,
                f_discount,
                vol * sqrt_t,
            ).strike_from_delta(delta)
            points.setdefault(strike, vol)
            col += 1
        if self.has_atm:
            vol = self._column_vol(col, t)
            strike = BlackDeltaCalculator(
                -1,
                self.delta_type,
                self.spot,
                d_discount,
                f_discount,
                vol * sqrt_t,
            ).atm_strike(self.atm_type)
            points.setdefault(strike, vol)
            col += 1
        for delta in self.call_deltas:
            vol = self._column_vol(col, t)
            strike = BlackDeltaCalculator(
                1,
                self.delta_type,
                self.spot,
                d_discount,
                f_discount,
                vol * sqrt_t,
            ).strike_from_delta(delta)
            points.setdefault(strike, vol)
            col += 1
        ordered = sorted(points.items())
        return [p[0] for p in ordered], [p[1] for p in ordered]

    def _column_vol(self, column: int, t: float) -> float:
        vols = tuple(row[column] for row in self.volatilities)
        return _black_variance_curve_vol_time(self.reference_date, self.dates, vols, self.day_counter, t)

    def _atm_or_middle_vol(self, t: float) -> float:
        if self.has_atm:
            return self._column_vol(len(self.put_deltas), t)
        middle = (len(self.put_deltas) + len(self.call_deltas)) // 2
        return self._column_vol(middle, t)


def _black_variance_curve_vol_time(
    reference_date: date,
    dates: tuple[date, ...],
    volatilities: tuple[float, ...],
    day_counter: DayCounter,
    t: float,
) -> float:
    return BlackVarianceCurve(
        reference_date,
        dates,
        volatilities,
        day_counter,
        force_monotone_variance=False,
    ).black_vol_time(t)
