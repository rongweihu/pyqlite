from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date

from pyquantlib.engines.black_swaption import SwaptionResult
from pyquantlib.instruments.bermudan_swaption import BermudanSwaption
from pyquantlib.instruments.swap import SwapType
from pyquantlib.instruments.swaption import SettlementType
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.volatility import BlackConstantVol


@dataclass(frozen=True)
class LsmBermudanSwaptionEngine:
    discount_curve: YieldCurve
    volatility: BlackConstantVol
    paths: int = 2048
    seed: int = 42

    def calculate(self, swaption: BermudanSwaption) -> SwaptionResult:
        if swaption.settlement_type != SettlementType.PHYSICAL:
            raise ValueError("only physical settlement is supported")
        exercise_dates = tuple(d for d in swaption.exercise_dates if d >= self.discount_curve.reference_date)
        if not exercise_dates:
            return SwaptionResult(0.0, 0.0, 0.0, swaption.swap.fixed_rate, 0.0, 0.0, 0.0, 0.0, 0.0)
        rng = random.Random(self.seed)
        t = [self.discount_curve.time_from_reference(d) for d in exercise_dates]
        initial_swap_rate = _forward_swap_rate(swaption.swap, self.discount_curve, exercise_dates[0])
        sigma = self.volatility.black_vol(exercise_dates[-1], swaption.swap.fixed_rate)
        paths = [_simulate_lognormal_path(initial_swap_rate, sigma, t, rng) for _ in range(self.paths)]
        values = [_exercise_value(swaption, exercise_dates[-1], path[-1], self.discount_curve) for path in paths]
        exercise_index = len(exercise_dates) - 1
        for i in range(len(exercise_dates) - 2, -1, -1):
            dt = max(t[i + 1] - t[i], 0.0)
            df = self.discount_curve.discount(exercise_dates[i + 1]) / self.discount_curve.discount(exercise_dates[i])
            discounted = [v * df for v in values]
            intrinsic = [_exercise_value(swaption, exercise_dates[i], path[i], self.discount_curve) for path in paths]
            itm = [j for j, x in enumerate(intrinsic) if x > 0.0]
            if len(itm) >= 3:
                coeffs = _quadratic_regression([paths[j][i] for j in itm], [discounted[j] for j in itm])
                continuation = [_poly(coeffs, paths[j][i]) for j in range(len(paths))]
            else:
                continuation = discounted
            values = [intrinsic[j] if intrinsic[j] > continuation[j] else discounted[j] for j in range(len(paths))]
            if any(intrinsic[j] > continuation[j] for j in range(len(paths))):
                exercise_index = i
        value = sum(values) / len(values) * self.discount_curve.discount(exercise_dates[0])
        strike = swaption.swap.fixed_rate
        atm = initial_swap_rate
        expiry = exercise_dates[exercise_index]
        time_to_expiry = max(self.discount_curve.time_from_reference(expiry), 0.0)
        annuity = _annuity(swaption.swap, self.discount_curve, expiry)
        return SwaptionResult(value, annuity, atm, strike, sigma * math.sqrt(time_to_expiry), 0.0, 0.0, time_to_expiry, value / self.discount_curve.discount(exercise_dates[0]))


def _simulate_lognormal_path(initial: float, sigma: float, times: list[float], rng: random.Random) -> list[float]:
    result = []
    previous_t = 0.0
    value = max(initial, 1.0e-8)
    for t in times:
        dt = max(t - previous_t, 0.0)
        if dt > 0.0 and sigma > 0.0:
            z = rng.gauss(0.0, 1.0)
            value *= math.exp(-0.5 * sigma * sigma * dt + sigma * math.sqrt(dt) * z)
        result.append(value)
        previous_t = t
    return result


def _annuity(swap, curve: YieldCurve, exercise_date: date) -> float:
    exercise_df = curve.discount(exercise_date)
    total = 0.0
    for coupon in swap.fixed_leg:
        if coupon.payment_date > exercise_date:
            total += coupon.nominal * coupon.accrual_period * curve.discount(coupon.payment_date) / exercise_df
    return total


def _forward_swap_rate(swap, curve: YieldCurve, exercise_date: date) -> float:
    annuity = _annuity(swap, curve, exercise_date)
    if annuity == 0.0:
        return 0.0
    floating_pv = 0.0
    exercise_df = curve.discount(exercise_date)
    for coupon in swap.floating_leg:
        if coupon.payment_date > exercise_date:
            floating_pv += coupon.amount * curve.discount(coupon.payment_date) / exercise_df
    return max(floating_pv / annuity, 1.0e-8)


def _exercise_value(swaption: BermudanSwaption, exercise_date: date, swap_rate: float, curve: YieldCurve) -> float:
    sign = 1.0 if swaption.swap.swap_type == SwapType.PAYER else -1.0
    return _annuity(swaption.swap, curve, exercise_date) * max(sign * (swap_rate - swaption.swap.fixed_rate), 0.0)


def _quadratic_regression(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    n = float(len(xs))
    sx = sum(xs)
    sx2 = sum(x * x for x in xs)
    sx3 = sum(x * x * x for x in xs)
    sx4 = sum(x * x * x * x for x in xs)
    sy = sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sx2y = sum(x * x * y for x, y in zip(xs, ys))
    return _solve3(((n, sx, sx2), (sx, sx2, sx3), (sx2, sx3, sx4)), (sy, sxy, sx2y))


def _solve3(a, b) -> tuple[float, float, float]:
    m = [list(a[0]) + [b[0]], list(a[1]) + [b[1]], list(a[2]) + [b[2]]]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1.0e-14:
            return (sum(b) / len(b), 0.0, 0.0)
        m[col], m[pivot] = m[pivot], m[col]
        divisor = m[col][col]
        for j in range(col, 4):
            m[col][j] /= divisor
        for r in range(3):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, 4):
                m[r][j] -= factor * m[col][j]
    return (m[0][3], m[1][3], m[2][3])


def _poly(coeffs: tuple[float, float, float], x: float) -> float:
    return coeffs[0] + coeffs[1] * x + coeffs[2] * x * x
