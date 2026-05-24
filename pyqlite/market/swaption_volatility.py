from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from pyqlite.time.date import Period, TimeUnit, advance_date
from pyqlite.time.daycounter import Actual365Fixed, DayCounter


@dataclass(frozen=True)
class ConstantSwaptionVolatility:
    reference_date: date
    volatility: float
    day_counter: DayCounter = Actual365Fixed()
    shift_value: float = 0.0

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def volatility_value(self, option_date: date, swap_length: float, strike: float | None = None) -> float:
        return self.volatility

    def black_variance(self, option_date: date, swap_length: float | None = None, strike: float | None = None) -> float:
        t = max(self.time_from_reference(option_date), 0.0)
        return self.volatility * self.volatility * t

    def shift(self, option_date: date, swap_length: float | None = None) -> float:
        return self.shift_value


@dataclass(frozen=True)
class SwaptionVolatilityMatrix:
    """ATM swaption volatility matrix indexed by option expiry and swap tenor.

    This mirrors QuantLib's `SwaptionVolatilityMatrix`: rows are option
    expiries, columns are swap tenors, and interpolation is bilinear in
    option time and swap length.
    """

    reference_date: date
    option_tenors: tuple[Period, ...]
    swap_tenors: tuple[Period, ...]
    volatilities: tuple[tuple[float, ...], ...]
    day_counter: DayCounter = Actual365Fixed()
    shifts: tuple[tuple[float, ...], ...] = ()
    flat_extrapolation: bool = False

    def __post_init__(self) -> None:
        if not self.option_tenors or not self.swap_tenors:
            raise ValueError("swaption volatility matrix requires option and swap tenors")
        if len(self.volatilities) != len(self.option_tenors):
            raise ValueError("volatility rows must match option tenors")
        for row in self.volatilities:
            if len(row) != len(self.swap_tenors):
                raise ValueError("volatility columns must match swap tenors")
            if any(vol < 0.0 for vol in row):
                raise ValueError("volatilities must be non-negative")
        if self.shifts:
            if len(self.shifts) != len(self.option_tenors):
                raise ValueError("shift rows must match option tenors")
            for row in self.shifts:
                if len(row) != len(self.swap_tenors):
                    raise ValueError("shift columns must match swap tenors")
        option_times = self.option_times
        swap_lengths = self.swap_lengths
        if tuple(sorted(option_times)) != option_times:
            raise ValueError("option tenors must be sorted")
        if tuple(sorted(swap_lengths)) != swap_lengths:
            raise ValueError("swap tenors must be sorted")

    @property
    def option_times(self) -> tuple[float, ...]:
        return tuple(self.time_from_reference(advance_date(self.reference_date, tenor)) for tenor in self.option_tenors)

    @property
    def swap_lengths(self) -> tuple[float, ...]:
        return tuple(_period_to_years(tenor) for tenor in self.swap_tenors)

    def time_from_reference(self, d: date) -> float:
        return self.day_counter.year_fraction(self.reference_date, d)

    def volatility_value(self, option_date: date, swap_length: float, strike: float | None = None) -> float:
        return _bilinear(
            self.swap_lengths,
            self.option_times,
            self.volatilities,
            swap_length,
            max(self.time_from_reference(option_date), 0.0),
            self.flat_extrapolation,
        )

    def black_variance(self, option_date: date, swap_length: float, strike: float | None = None) -> float:
        t = max(self.time_from_reference(option_date), 0.0)
        vol = self.volatility_value(option_date, swap_length, strike)
        return vol * vol * t

    def shift(self, option_date: date, swap_length: float) -> float:
        if not self.shifts:
            return 0.0
        return _bilinear(
            self.swap_lengths,
            self.option_times,
            self.shifts,
            swap_length,
            max(self.time_from_reference(option_date), 0.0),
            self.flat_extrapolation,
        )


@dataclass(frozen=True)
class SwaptionVolatilityCube:
    """Strike-spread swaption smile cube over an ATM volatility matrix.

    QuantLib stores smile quotes as spreads over the ATM vol at strike spreads
    from the ATM swap rate. This class follows that convention and linearly
    interpolates the local smile by strike after bilinear interpolation of each
    strike-spread layer.
    """

    atm_vol: SwaptionVolatilityMatrix
    strike_spreads: tuple[float, ...]
    vol_spreads: tuple[tuple[tuple[float, ...], ...], ...]

    def __post_init__(self) -> None:
        if not self.strike_spreads:
            raise ValueError("swaption volatility cube requires strike spreads")
        if tuple(sorted(self.strike_spreads)) != self.strike_spreads:
            raise ValueError("strike spreads must be sorted")
        expected_rows = len(self.atm_vol.option_tenors)
        expected_cols = len(self.atm_vol.swap_tenors)
        if len(self.vol_spreads) != len(self.strike_spreads):
            raise ValueError("one vol-spread matrix is required for each strike spread")
        for layer in self.vol_spreads:
            if len(layer) != expected_rows:
                raise ValueError("vol-spread rows must match option tenors")
            for row in layer:
                if len(row) != expected_cols:
                    raise ValueError("vol-spread columns must match swap tenors")

    def time_from_reference(self, d: date) -> float:
        return self.atm_vol.time_from_reference(d)

    def volatility_value(self, option_date: date, swap_length: float, strike: float | None = None, atm_forward: float | None = None) -> float:
        atm_vol = self.atm_vol.volatility_value(option_date, swap_length, strike)
        if strike is None or atm_forward is None:
            return atm_vol
        spreads = []
        for layer in self.vol_spreads:
            spreads.append(
                _bilinear(
                    self.atm_vol.swap_lengths,
                    self.atm_vol.option_times,
                    layer,
                    swap_length,
                    max(self.time_from_reference(option_date), 0.0),
                    self.atm_vol.flat_extrapolation,
                )
            )
        return max(0.0, atm_vol + _linear_extrapolate(self.strike_spreads, tuple(spreads), strike - atm_forward))

    def black_variance(
        self,
        option_date: date,
        swap_length: float,
        strike: float | None = None,
        atm_forward: float | None = None,
    ) -> float:
        t = max(self.time_from_reference(option_date), 0.0)
        vol = self.volatility_value(option_date, swap_length, strike, atm_forward)
        return vol * vol * t

    def shift(self, option_date: date, swap_length: float) -> float:
        return self.atm_vol.shift(option_date, swap_length)


@dataclass(frozen=True)
class SabrParameters:
    alpha: float
    beta: float
    nu: float
    rho: float


@dataclass(frozen=True)
class SabrSwaptionVolatilityCube:
    """Swaption smile cube backed by SABR parameter surfaces.

    This is the fit-early/interpolate-later form used by QuantLib's
    `SabrSwaptionVolatilityCube`, scoped to supplied SABR parameters rather
    than doing optimizer calibration inside the package.
    """

    atm_vol: SwaptionVolatilityMatrix
    parameters: tuple[tuple[SabrParameters, ...], ...]
    shift_value: float = 0.0

    def __post_init__(self) -> None:
        if len(self.parameters) != len(self.atm_vol.option_tenors):
            raise ValueError("SABR parameter rows must match option tenors")
        for row in self.parameters:
            if len(row) != len(self.atm_vol.swap_tenors):
                raise ValueError("SABR parameter columns must match swap tenors")
            for params in row:
                validate_sabr_parameters(params.alpha, params.beta, params.nu, params.rho)

    def time_from_reference(self, d: date) -> float:
        return self.atm_vol.time_from_reference(d)

    def volatility_value(self, option_date: date, swap_length: float, strike: float | None = None, atm_forward: float | None = None) -> float:
        if strike is None or atm_forward is None:
            return self.atm_vol.volatility_value(option_date, swap_length, strike)
        t = max(self.time_from_reference(option_date), 0.0)
        alpha = self._parameter_value(option_date, swap_length, "alpha")
        beta = self._parameter_value(option_date, swap_length, "beta")
        nu = self._parameter_value(option_date, swap_length, "nu")
        rho = self._parameter_value(option_date, swap_length, "rho")
        return shifted_sabr_volatility(strike, atm_forward, t, alpha, beta, nu, rho, self.shift_value)

    def black_variance(
        self,
        option_date: date,
        swap_length: float,
        strike: float | None = None,
        atm_forward: float | None = None,
    ) -> float:
        t = max(self.time_from_reference(option_date), 0.0)
        vol = self.volatility_value(option_date, swap_length, strike, atm_forward)
        return vol * vol * t

    def shift(self, option_date: date, swap_length: float) -> float:
        return self.shift_value

    def _parameter_value(self, option_date: date, swap_length: float, field: str) -> float:
        values = tuple(tuple(getattr(params, field) for params in row) for row in self.parameters)
        return _bilinear(
            self.atm_vol.swap_lengths,
            self.atm_vol.option_times,
            values,
            swap_length,
            max(self.time_from_reference(option_date), 0.0),
            self.atm_vol.flat_extrapolation,
        )


def shifted_sabr_volatility(
    strike: float,
    forward: float,
    expiry_time: float,
    alpha: float,
    beta: float,
    nu: float,
    rho: float,
    shift: float = 0.0,
) -> float:
    if strike + shift <= 0.0:
        raise ValueError("strike + shift must be positive")
    if forward + shift <= 0.0:
        raise ValueError("forward + shift must be positive")
    if expiry_time < 0.0:
        raise ValueError("expiry time must be non-negative")
    validate_sabr_parameters(alpha, beta, nu, rho)
    return unsafe_sabr_lognormal_volatility(strike + shift, forward + shift, expiry_time, alpha, beta, nu, rho)


def unsafe_sabr_lognormal_volatility(
    strike: float,
    forward: float,
    expiry_time: float,
    alpha: float,
    beta: float,
    nu: float,
    rho: float,
) -> float:
    one_minus_beta = 1.0 - beta
    a = (forward * strike) ** one_minus_beta
    sqrt_a = math.sqrt(a)
    if not math.isclose(forward, strike, rel_tol=0.0, abs_tol=1.0e-12):
        log_m = math.log(forward / strike)
    else:
        epsilon = (forward - strike) / strike
        log_m = epsilon - 0.5 * epsilon * epsilon
    z = (nu / alpha) * sqrt_a * log_m
    b = 1.0 - 2.0 * rho * z + z * z
    c = one_minus_beta * one_minus_beta * log_m * log_m
    xx = math.log((math.sqrt(b) + z - rho) / (1.0 - rho))
    d = sqrt_a * (1.0 + c / 24.0 + c * c / 1920.0)
    correction = 1.0 + expiry_time * (
        one_minus_beta * one_minus_beta * alpha * alpha / (24.0 * a)
        + 0.25 * rho * beta * nu * alpha / sqrt_a
        + (2.0 - 3.0 * rho * rho) * nu * nu / 24.0
    )
    if abs(z * z) > 10.0 * 1.0e-16:
        multiplier = z / xx
    else:
        multiplier = 1.0 - 0.5 * rho * z - (3.0 * rho * rho - 2.0) * z * z / 12.0
    return (alpha / d) * multiplier * correction


def validate_sabr_parameters(alpha: float, beta: float, nu: float, rho: float) -> None:
    if alpha <= 0.0:
        raise ValueError("alpha must be positive")
    if beta < 0.0 or beta > 1.0:
        raise ValueError("beta must be between 0 and 1")
    if nu < 0.0:
        raise ValueError("nu must be non-negative")
    if rho * rho >= 1.0:
        raise ValueError("rho square must be less than one")


def _period_to_years(period: Period) -> float:
    if period.unit == TimeUnit.DAYS:
        return period.length / 365.0
    if period.unit == TimeUnit.WEEKS:
        return period.length * 7.0 / 365.0
    if period.unit == TimeUnit.MONTHS:
        return period.length / 12.0
    if period.unit == TimeUnit.YEARS:
        return float(period.length)
    raise ValueError(f"unsupported period unit: {period.unit}")


def _bilinear(
    xs: tuple[float, ...],
    ys: tuple[float, ...],
    values: tuple[tuple[float, ...], ...],
    x: float,
    y: float,
    flat_extrapolation: bool,
) -> float:
    x0, x1, ix = _bracket(xs, x)
    y0, y1, iy = _bracket(ys, y)
    if flat_extrapolation:
        x = min(max(x, xs[0]), xs[-1])
        y = min(max(y, ys[0]), ys[-1])
    q00 = values[iy][ix]
    q10 = values[iy][ix + (1 if x1 != x0 else 0)]
    q01 = values[iy + (1 if y1 != y0 else 0)][ix]
    q11 = values[iy + (1 if y1 != y0 else 0)][ix + (1 if x1 != x0 else 0)]
    if x1 == x0 and y1 == y0:
        return q00
    if x1 == x0:
        return _linear(y0, q00, y1, q01, y)
    if y1 == y0:
        return _linear(x0, q00, x1, q10, x)
    wx = (x - x0) / (x1 - x0)
    wy = (y - y0) / (y1 - y0)
    return (1.0 - wx) * (1.0 - wy) * q00 + wx * (1.0 - wy) * q10 + (1.0 - wx) * wy * q01 + wx * wy * q11


def _bracket(values: tuple[float, ...], x: float) -> tuple[float, float, int]:
    if len(values) == 1:
        return values[0], values[0], 0
    if x <= values[0]:
        return values[0], values[1], 0
    if x >= values[-1]:
        return values[-2], values[-1], len(values) - 2
    for i in range(1, len(values)):
        if x <= values[i]:
            return values[i - 1], values[i], i - 1
    raise RuntimeError("unreachable interpolation bracket")


def _linear(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 == x0:
        return y1
    return y0 + (x - x0) / (x1 - x0) * (y1 - y0)


def _linear_extrapolate(xs: tuple[float, ...], ys: tuple[float, ...], x: float) -> float:
    if len(xs) == 1:
        return ys[0]
    x0, x1, i = _bracket(xs, x)
    return _linear(x0, ys[i], x1, ys[i + 1], x)
