from __future__ import annotations

from dataclasses import dataclass

from pyqlite.engines.pricing_result import PricingResult
from pyqlite.instruments.fra import PositionType
from pyqlite.instruments.variance import VarianceSwap, VolatilitySwap
from pyqlite.market.curves import YieldCurve
from pyqlite.market.volatility import BlackConstantVol


@dataclass(frozen=True)
class VarianceSwapEngine:
    volatility: BlackConstantVol
    discount_curve: YieldCurve

    def calculate(self, swap: VarianceSwap) -> PricingResult:
        start_time = max(self.volatility.time_from_reference(swap.start_date), 0.0)
        end_time = max(self.volatility.time_from_reference(swap.maturity_date), 0.0)
        period = end_time - start_time
        if period <= 0.0:
            raise ValueError("variance swap maturity_date must be after start_date")
        start_variance = self.volatility.black_variance_time(start_time, None)
        end_variance = self.volatility.black_variance_time(end_time, None)
        fair_variance = max(end_variance - start_variance, 0.0) / period
        sign = 1.0 if swap.position == PositionType.LONG else -1.0
        value = sign * swap.notional * (fair_variance - swap.strike) * self.discount_curve.discount(swap.maturity_date)
        return PricingResult(value, fair_variance)


@dataclass(frozen=True)
class VolatilitySwapEngine:
    volatility: BlackConstantVol
    discount_curve: YieldCurve

    def calculate(self, swap: VolatilitySwap) -> PricingResult:
        fair_variance = VarianceSwapEngine(self.volatility, self.discount_curve).calculate(
            VarianceSwap(swap.position, swap.strike * swap.strike, swap.notional, swap.start_date, swap.maturity_date)
        ).fair_value
        fair_vol = fair_variance ** 0.5
        sign = 1.0 if swap.position == PositionType.LONG else -1.0
        value = sign * swap.notional * (fair_vol - swap.strike) * self.discount_curve.discount(swap.maturity_date)
        return PricingResult(value, fair_vol)
