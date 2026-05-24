from __future__ import annotations

from dataclasses import dataclass

from pyqlite.engines.pricing_result import PricingResult
from pyqlite.instruments.inflation import YearOnYearInflationSwap, ZeroCouponInflationSwap
from pyqlite.instruments.swap import SwapType
from pyqlite.market.curves import YieldCurve
from pyqlite.market.inflation import InflationIndexCurve, ZeroInflationCurve


@dataclass(frozen=True)
class DiscountingInflationSwapEngine:
    inflation_curve: ZeroInflationCurve | InflationIndexCurve
    discount_curve: YieldCurve

    def calculate_zero_coupon(self, swap: ZeroCouponInflationSwap) -> PricingResult:
        t = swap.day_counter.year_fraction(swap.start_date, swap.maturity_date)
        if t <= 0.0:
            raise ValueError("zero-coupon inflation swap maturity_date must be after start_date")
        inflation_ratio = self.inflation_curve.index_fixing(swap.maturity_date) / swap.base_index
        fixed_ratio = (1.0 + swap.fixed_rate) ** t
        inflation_leg = swap.notional * (inflation_ratio - 1.0) * self.discount_curve.discount(swap.maturity_date)
        fixed_leg = swap.notional * (fixed_ratio - 1.0) * self.discount_curve.discount(swap.maturity_date)
        sign = 1.0 if swap.swap_type == SwapType.RECEIVER else -1.0
        fair_rate = inflation_ratio ** (1.0 / t) - 1.0
        return PricingResult(sign * inflation_leg - sign * fixed_leg, fair_rate, sign * inflation_leg, -sign * fixed_leg)

    def calculate_year_on_year(self, swap: YearOnYearInflationSwap) -> PricingResult:
        fixed_leg = 0.0
        yoy_leg = 0.0
        annuity = 0.0
        previous_index = swap.base_index
        for start, end in zip(swap.schedule.dates[:-1], swap.schedule.dates[1:]):
            tau = swap.day_counter.year_fraction(start, end)
            df = self.discount_curve.discount(end)
            index = self.inflation_curve.index_fixing(end)
            yoy = index / previous_index - 1.0
            fixed_leg += swap.notional * swap.fixed_rate * tau * df
            yoy_leg += swap.notional * (yoy + swap.spread) * tau * df
            annuity += swap.notional * tau * df
            previous_index = index
        sign = 1.0 if swap.swap_type == SwapType.RECEIVER else -1.0
        fair_rate = 0.0 if annuity == 0.0 else yoy_leg / annuity
        return PricingResult(sign * yoy_leg - sign * fixed_leg, fair_rate, sign * yoy_leg, -sign * fixed_leg)
