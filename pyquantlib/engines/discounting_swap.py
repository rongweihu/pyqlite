from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.cashflows.analytics import leg_npv_bps
from pyquantlib.instruments.swap import VanillaSwap
from pyquantlib.market.curves import YieldCurve


@dataclass(frozen=True)
class SwapResult:
    value: float
    fixed_leg_npv: float
    floating_leg_npv: float
    fixed_leg_bps: float
    floating_leg_bps: float
    fair_rate: float
    fair_spread: float


@dataclass(frozen=True)
class DiscountingSwapEngine:
    discount_curve: YieldCurve
    include_settlement_date_flows: bool = False
    settlement_date: date | None = None
    npv_date: date | None = None

    def calculate(self, swap: VanillaSwap) -> SwapResult:
        settlement_date = self.settlement_date or self.discount_curve.reference_date
        npv_date = self.npv_date or self.discount_curve.reference_date
        signed_npvs = []
        signed_bps = []
        for leg, sign in zip(swap.legs, swap.payer_signs):
            npv, bps = leg_npv_bps(
                leg,
                self.discount_curve,
                settlement_date,
                npv_date,
                self.include_settlement_date_flows,
            )
            signed_npvs.append(sign * npv)
            signed_bps.append(sign * bps)

        value = sum(signed_npvs)
        fixed_sign = swap.payer_signs[0]
        floating_sign = swap.payer_signs[1]
        fixed_unsigned_bps = signed_bps[0] / fixed_sign if fixed_sign else 0.0
        floating_unsigned_bps = signed_bps[1] / floating_sign if floating_sign else 0.0

        fixed_rate_bps = fixed_unsigned_bps / 1.0e-4
        current_fixed_rate = getattr(swap, "fixed_rate", 0.0)
        if not isinstance(current_fixed_rate, (int, float)):
            current_fixed_rate = 0.0
        fair_rate = 0.0 if fixed_rate_bps == 0.0 else current_fixed_rate - value / (fixed_sign * fixed_rate_bps)

        spread_bps = floating_unsigned_bps / 1.0e-4
        current_spread = getattr(swap, "spread", 0.0)
        if not isinstance(current_spread, (int, float)):
            current_spread = 0.0
        fair_spread = 0.0 if spread_bps == 0.0 else current_spread - value / (floating_sign * spread_bps)

        return SwapResult(
            value=value,
            fixed_leg_npv=signed_npvs[0],
            floating_leg_npv=signed_npvs[1],
            fixed_leg_bps=signed_bps[0],
            floating_leg_bps=signed_bps[1],
            fair_rate=fair_rate,
            fair_spread=fair_spread,
        )
