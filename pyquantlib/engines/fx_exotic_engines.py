from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date
from typing import Callable

from pyquantlib.instruments.fx_exotics import (
    AsianFxOption,
    BarrierDirection,
    BarrierFxOption,
    BarrierStyle,
    BasketFxOption,
    CliquetFxOption,
    DigitalFxOption,
    DoubleBarrierFxOption,
    ForwardStartFxOption,
    LookbackFxOption,
    QuantoFxOption,
    WindowBarrierFxOption,
)
from pyquantlib.instruments.fx_option import OptionType
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.quote import SimpleQuote
from pyquantlib.market.volatility import BlackConstantVol
from pyquantlib.math.distributions import normal_cdf


@dataclass(frozen=True)
class FxExoticResult:
    value: float
    standard_error: float = 0.0
    paths: int = 0


@dataclass(frozen=True)
class AnalyticDigitalFxOptionEngine:
    spot_fx: SimpleQuote
    domestic_curve: YieldCurve
    foreign_curve: YieldCurve
    volatility: BlackConstantVol

    def calculate(self, option: DigitalFxOption) -> FxExoticResult:
        spot = self.spot_fx.value
        domestic_df = self.domestic_curve.discount(option.expiry_date)
        foreign_df = self.foreign_curve.discount(option.expiry_date)
        forward = spot * foreign_df / domestic_df
        variance = self.volatility.black_variance(option.expiry_date, option.strike)
        stddev = math.sqrt(max(variance, 0.0))
        if stddev == 0.0:
            probability = 1.0 if option.option_type.value * (forward - option.strike) > 0.0 else 0.0
        else:
            d2 = math.log(forward / option.strike) / stddev - 0.5 * stddev
            probability = normal_cdf(option.option_type.value * d2)
        return FxExoticResult(option.notional * option.cash_payoff * domestic_df * probability)


@dataclass(frozen=True)
class McFxExoticEngine:
    spot_fx: SimpleQuote
    domestic_curve: YieldCurve
    foreign_curve: YieldCurve
    volatility: BlackConstantVol
    paths: int = 8192
    steps: int = 128
    seed: int = 42

    def calculate_barrier(self, option: BarrierFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _barrier_payoff(option, path),
        )

    def calculate_double_barrier(self, option: DoubleBarrierFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _double_barrier_payoff(option, path),
        )

    def calculate_asian(self, option: AsianFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _asian_payoff(option, path),
        )

    def calculate_window_barrier(self, option: WindowBarrierFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _window_barrier_payoff(option, path, times, self.volatility.reference_date),
        )

    def calculate_forward_start(self, option: ForwardStartFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _forward_start_payoff(option, path, times, self.volatility.reference_date),
        )

    def calculate_quanto(self, option: QuantoFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _quanto_payoff(option, path),
            drift_adjustment=option.quanto_drift_adjustment,
            payoff_multiplier=option.quanto_fx_rate,
        )

    def calculate_lookback(self, option: LookbackFxOption) -> FxExoticResult:
        return self._single_path_value(
            option.expiry_date,
            lambda path, times: _lookback_payoff(option, path),
        )

    def calculate_cliquet(self, option: CliquetFxOption) -> FxExoticResult:
        expiry = option.reset_dates[-1]
        return self._single_path_value(
            expiry,
            lambda path, times: _cliquet_payoff(option, path, times, self.volatility.reference_date),
        )

    def calculate_basket(self, option: BasketFxOption) -> FxExoticResult:
        t = self.volatility.time_from_reference(option.expiry_date)
        if t <= 0.0:
            payoff = max(option.option_type.value * (sum(w * s for w, s in zip(option.weights, option.spots)) - option.strike), 0.0)
            return FxExoticResult(option.notional * payoff)
        domestic_df = self.domestic_curve.discount(option.expiry_date)
        rd = -math.log(domestic_df) / t
        normals = _cholesky(option.correlation)
        rng = random.Random(self.seed)
        payoffs = []
        for _ in range(self.paths):
            z = _correlated_normals(normals, rng)
            basket = 0.0
            for i, spot in enumerate(option.spots):
                foreign_df = option.foreign_discounts[i]
                rf = -math.log(foreign_df) / t
                vol = option.volatilities[i]
                terminal = spot * math.exp((rd - rf - 0.5 * vol * vol) * t + vol * math.sqrt(t) * z[i])
                basket += option.weights[i] * terminal
            payoffs.append(option.notional * max(option.option_type.value * (basket - option.strike), 0.0))
        return _discounted_result(payoffs, domestic_df)

    def _single_path_value(
        self,
        expiry: date,
        payoff: Callable[[list[float], list[float]], float],
        drift_adjustment: float = 0.0,
        payoff_multiplier: float = 1.0,
    ) -> FxExoticResult:
        t = self.volatility.time_from_reference(expiry)
        if t <= 0.0:
            return FxExoticResult(0.0)
        domestic_df = self.domestic_curve.discount(expiry)
        foreign_df = self.foreign_curve.discount(expiry)
        rd = -math.log(domestic_df) / t
        rf = -math.log(foreign_df) / t
        vol = self.volatility.black_vol(expiry)
        rng = random.Random(self.seed)
        dt = t / self.steps
        times = [(i + 1) * dt for i in range(self.steps)]
        payoffs = []
        for _ in range(self.paths):
            s = self.spot_fx.value
            path = []
            for _step in range(self.steps):
                z = rng.gauss(0.0, 1.0)
                s *= math.exp((rd - rf + drift_adjustment - 0.5 * vol * vol) * dt + vol * math.sqrt(dt) * z)
                path.append(s)
            payoffs.append(payoff_multiplier * payoff(path, times))
        return _discounted_result(payoffs, domestic_df)


def _barrier_payoff(option: BarrierFxOption, path: list[float]) -> float:
    touched = _barrier_touched(path, option.direction, option.barrier)
    active = touched if option.style == BarrierStyle.KNOCK_IN else not touched
    if active:
        return option.notional * max(option.option_type.value * (path[-1] - option.strike), 0.0)
    return option.notional * option.rebate


def _double_barrier_payoff(option: DoubleBarrierFxOption, path: list[float]) -> float:
    touched = any(s <= option.lower_barrier or s >= option.upper_barrier for s in path)
    pays = touched if option.knock_in else not touched
    return option.notional * option.cash_payoff if pays else 0.0


def _asian_payoff(option: AsianFxOption, path: list[float]) -> float:
    total = option.running_accumulator + sum(path)
    count = option.past_fixings + len(path)
    average = total / count
    return option.notional * max(option.option_type.value * (average - option.strike), 0.0)


def _window_barrier_payoff(option: WindowBarrierFxOption, path: list[float], times: list[float], reference_date: date) -> float:
    start_t = (option.window_start - reference_date).days / 365.0
    end_t = (option.window_end - reference_date).days / 365.0
    window_path = [s for s, t in zip(path, times) if start_t <= t <= end_t]
    touched = _barrier_touched(window_path, option.direction, option.barrier) if window_path else False
    active = touched if option.style == BarrierStyle.KNOCK_IN else not touched
    if active:
        return option.notional * max(option.option_type.value * (path[-1] - option.strike), 0.0)
    return option.notional * option.rebate


def _forward_start_payoff(option: ForwardStartFxOption, path: list[float], times: list[float], reference_date: date) -> float:
    reset_t = (option.reset_date - reference_date).days / 365.0
    reset_index = min(range(len(times)), key=lambda i: abs(times[i] - reset_t))
    strike = option.moneyness * path[reset_index]
    return option.notional * max(option.option_type.value * (path[-1] - strike), 0.0)


def _quanto_payoff(option: QuantoFxOption, path: list[float]) -> float:
    return option.notional * max(option.option_type.value * (path[-1] - option.strike), 0.0)


def _lookback_payoff(option: LookbackFxOption, path: list[float]) -> float:
    if option.option_type == OptionType.CALL:
        return option.notional * max(max(path) - option.strike, 0.0)
    return option.notional * max(option.strike - min(path), 0.0)


def _cliquet_payoff(option: CliquetFxOption, path: list[float], times: list[float], reference_date: date) -> float:
    last = path[0]
    returns = []
    for reset_date in option.reset_dates:
        reset_t = (reset_date - reference_date).days / 365.0
        idx = min(range(len(times)), key=lambda i: abs(times[i] - reset_t))
        current = path[idx]
        returns.append(min(max(current / last - 1.0, option.local_floor), option.local_cap))
        last = current
    total = sum(returns)
    if option.global_floor is not None:
        total = max(total, option.global_floor)
    if option.global_cap is not None:
        total = min(total, option.global_cap)
    return option.notional * total


def _barrier_touched(path: list[float], direction: BarrierDirection, barrier: float) -> bool:
    if direction == BarrierDirection.UP:
        return any(s >= barrier for s in path)
    return any(s <= barrier for s in path)


def _discounted_result(payoffs: list[float], discount: float) -> FxExoticResult:
    mean = sum(payoffs) / len(payoffs)
    if len(payoffs) < 2:
        error = 0.0
    else:
        variance = sum((x - mean) ** 2 for x in payoffs) / (len(payoffs) - 1)
        error = discount * math.sqrt(variance / len(payoffs))
    return FxExoticResult(discount * mean, error, len(payoffs))


def _cholesky(matrix: tuple[tuple[float, ...], ...]) -> list[list[float]]:
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            value = matrix[i][j] - sum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                lower[i][j] = math.sqrt(max(value, 0.0))
            else:
                lower[i][j] = value / lower[j][j]
    return lower


def _correlated_normals(cholesky: list[list[float]], rng: random.Random) -> list[float]:
    z = [rng.gauss(0.0, 1.0) for _ in cholesky]
    return [sum(row[j] * z[j] for j in range(len(row))) for row in cholesky]
