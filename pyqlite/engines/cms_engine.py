from __future__ import annotations

from dataclasses import dataclass

from pyqlite.engines.discounting_swap import SwapResult
from pyqlite.instruments.cms import CmsSwap
from pyqlite.instruments.swap import SwapType
from pyqlite.market.curves import YieldCurve
from pyqlite.market.swaption_volatility import SwaptionVolatilityMatrix
from pyqlite.time.date import advance_date


@dataclass(frozen=True)
class DiscountingCmsSwapEngine:
    discount_curve: YieldCurve
    forward_curve: YieldCurve
    swaption_volatility: SwaptionVolatilityMatrix | None = None

    def calculate(self, swap: CmsSwap) -> SwapResult:
        fixed_npv = 0.0
        fixed_bps = 0.0
        for start, end in zip(swap.fixed_schedule.dates[:-1], swap.fixed_schedule.dates[1:]):
            tau = swap.fixed_day_counter.year_fraction(start, end)
            df = self.discount_curve.discount(end)
            fixed_npv += swap.nominal * swap.fixed_rate * tau * df
            fixed_bps += swap.nominal * tau * 1.0e-4 * df
        cms_npv = 0.0
        cms_bps = 0.0
        for start, end in zip(swap.cms_schedule.dates[:-1], swap.cms_schedule.dates[1:]):
            tau = swap.cms_day_counter.year_fraction(start, end)
            df = self.discount_curve.discount(end)
            swap_end = advance_date(start, swap.cms_tenor)
            cms_rate = self.forward_curve.forward_rate(start, swap_end)
            if self.swaption_volatility is not None:
                option_time = max(self.discount_curve.time_from_reference(start), 0.0)
                swap_length = self.discount_curve.time_from_reference(swap_end) - self.discount_curve.time_from_reference(start)
                vol = self.swaption_volatility.volatility_value(start, swap_length, cms_rate)
                cms_rate += 0.5 * cms_rate * vol * vol * option_time * max(swap_length, 0.0) / max(1.0 + cms_rate, 1.0e-8)
            cms_npv += swap.nominal * (swap.gearing * cms_rate + swap.spread) * tau * df
            cms_bps += swap.nominal * tau * 1.0e-4 * df
        if swap.swap_type == SwapType.PAYER:
            signed_fixed = -fixed_npv
            signed_cms = cms_npv
            fixed_sign = -1.0
            cms_sign = 1.0
        else:
            signed_fixed = fixed_npv
            signed_cms = -cms_npv
            fixed_sign = 1.0
            cms_sign = -1.0
        value = signed_fixed + signed_cms
        fair_rate = swap.fixed_rate - value / (fixed_sign * fixed_bps / 1.0e-4) if fixed_bps else 0.0
        fair_spread = swap.spread - value / (cms_sign * cms_bps / 1.0e-4) if cms_bps else 0.0
        return SwapResult(value, signed_fixed, signed_cms, fixed_sign * fixed_bps, cms_sign * cms_bps, fair_rate, fair_spread)
