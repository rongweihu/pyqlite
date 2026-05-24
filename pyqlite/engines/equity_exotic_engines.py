from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date

from pyqlite.engines.pricing_result import PricingResult
from pyqlite.instruments.equity_exotics import (
    BarrierDirection,
    BarrierStyle,
    EquityAsianOption,
    EquityBarrierOption,
    EquityBasketOption,
    EquityCliquetOption,
    EquityForwardStartOption,
    EquityLookbackOption,
)
from pyqlite.instruments.fx_option import OptionType
from pyqlite.market.curves import YieldCurve
from pyqlite.market.quote import SimpleQuote
from pyqlite.market.volatility import BlackConstantVol


@dataclass(frozen=True)
class McEquityExoticEngine:
    spot: SimpleQuote
    dividend_curve: YieldCurve
    risk_free_curve: YieldCurve
    volatility: BlackConstantVol
    paths: int = 4096
    steps: int = 64
    seed: int = 42

    def calculate_barrier(self, option: EquityBarrierOption) -> PricingResult:
        return self._single_path(option.expiry_date, lambda p, ts: _barrier_payoff(option, p))

    def calculate_asian(self, option: EquityAsianOption) -> PricingResult:
        return self._single_path(option.expiry_date, lambda p, ts: _asian_payoff(option, p, ts, self.risk_free_curve.reference_date))

    def calculate_lookback(self, option: EquityLookbackOption) -> PricingResult:
        return self._single_path(option.expiry_date, lambda p, ts: _lookback_payoff(option, p))

    def calculate_cliquet(self, option: EquityCliquetOption) -> PricingResult:
        return self._single_path(option.reset_dates[-1], lambda p, ts: _cliquet_payoff(option, p, ts, self.risk_free_curve.reference_date))

    def calculate_forward_start(self, option: EquityForwardStartOption) -> PricingResult:
        return self._single_path(option.expiry_date, lambda p, ts: _forward_start_payoff(option, p, ts, self.risk_free_curve.reference_date))

    def calculate_basket(self, option: EquityBasketOption) -> PricingResult:
        rng = random.Random(self.seed)
        expiry = option.expiry_date
        t = max(self.risk_free_curve.time_from_reference(expiry), 0.0)
        chol = _cholesky(option.correlation)
        vols = [self.volatility.black_vol(expiry, k) for k in option.spots]
        payoffs = []
        for _ in range(self.paths):
            zs = [rng.gauss(0.0, 1.0) for _ in option.spots]
            corr = [sum(chol[i][j] * zs[j] for j in range(i + 1)) for i in range(len(option.spots))]
            terminal = []
            for i, spot in enumerate(option.spots):
                rd = -math.log(self.risk_free_curve.discount(expiry)) / t if t > 0.0 else 0.0
                q = -math.log(self.dividend_curve.discount(expiry)) / t if t > 0.0 else 0.0
                terminal.append(spot * math.exp((rd - q - 0.5 * vols[i] * vols[i]) * t + vols[i] * math.sqrt(t) * corr[i]))
            basket = sum(qty * s for qty, s in zip(option.quantities, terminal))
            sign = 1.0 if option.option_type == OptionType.CALL else -1.0
            payoffs.append(max(sign * (basket - option.strike), 0.0))
        return PricingResult(sum(payoffs) / len(payoffs) * self.risk_free_curve.discount(expiry))

    def _single_path(self, expiry: date, payoff) -> PricingResult:
        rng = random.Random(self.seed)
        times = [max(self.risk_free_curve.time_from_reference(expiry) * i / self.steps, 0.0) for i in range(self.steps + 1)]
        maturity_time = times[-1]
        rd = -math.log(self.risk_free_curve.discount(expiry)) / maturity_time if maturity_time > 0.0 else 0.0
        q = -math.log(self.dividend_curve.discount(expiry)) / maturity_time if maturity_time > 0.0 else 0.0
        sigma = self.volatility.black_vol(expiry, None)
        payoffs = []
        for _ in range(self.paths):
            path = [self.spot.value]
            for i in range(1, len(times)):
                dt = times[i] - times[i - 1]
                z = rng.gauss(0.0, 1.0)
                path.append(path[-1] * math.exp((rd - q - 0.5 * sigma * sigma) * dt + sigma * math.sqrt(dt) * z))
            payoffs.append(payoff(path, times))
        return PricingResult(sum(payoffs) / len(payoffs) * self.risk_free_curve.discount(expiry))


def _barrier_payoff(option: EquityBarrierOption, path: list[float]) -> float:
    touched = max(path) >= option.barrier if option.direction == BarrierDirection.UP else min(path) <= option.barrier
    alive = touched if option.style == BarrierStyle.KNOCK_IN else not touched
    if not alive:
        return option.rebate * option.quantity
    sign = 1.0 if option.option_type == OptionType.CALL else -1.0
    return option.quantity * max(sign * (path[-1] - option.strike), 0.0)


def _asian_payoff(option: EquityAsianOption, path: list[float], times: list[float], reference_date: date) -> float:
    avg = sum(path) / len(path) if not option.fixing_dates else sum(path[min(int(i * (len(path) - 1) / max(len(option.fixing_dates), 1)), len(path) - 1)] for i, _ in enumerate(option.fixing_dates, 1)) / len(option.fixing_dates)
    sign = 1.0 if option.option_type == OptionType.CALL else -1.0
    return option.quantity * max(sign * (avg - option.strike), 0.0)


def _lookback_payoff(option: EquityLookbackOption, path: list[float]) -> float:
    if option.option_type == OptionType.CALL:
        return option.quantity * max(max(path) - option.strike, 0.0)
    return option.quantity * max(option.strike - min(path), 0.0)


def _cliquet_payoff(option: EquityCliquetOption, path: list[float], times: list[float], reference_date: date) -> float:
    n = len(option.reset_dates)
    previous = path[0]
    total = 0.0
    for i in range(1, n + 1):
        idx = min(int(i * (len(path) - 1) / n), len(path) - 1)
        ret = path[idx] / previous - 1.0
        total += min(max(ret, option.local_floor), option.local_cap)
        previous = path[idx]
    if option.global_floor is not None:
        total = max(total, option.global_floor)
    if option.global_cap is not None:
        total = min(total, option.global_cap)
    return option.quantity * total


def _forward_start_payoff(option: EquityForwardStartOption, path: list[float], times: list[float], reference_date: date) -> float:
    start_idx = max(0, min(len(path) - 1, int((len(path) - 1) / 2)))
    strike = option.moneyness * path[start_idx]
    sign = 1.0 if option.option_type == OptionType.CALL else -1.0
    return option.quantity * max(sign * (path[-1] - strike), 0.0)


def _cholesky(matrix: tuple[tuple[float, ...], ...]) -> list[list[float]]:
    n = len(matrix)
    result = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            value = matrix[i][j] - sum(result[i][k] * result[j][k] for k in range(j))
            result[i][j] = math.sqrt(max(value, 0.0)) if i == j else value / result[j][j]
    return result
