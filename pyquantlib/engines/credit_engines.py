from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from pyquantlib.instruments.credit import CdsOption, CreditDefaultSwap, ProtectionSide
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.default_curves import DefaultProbabilityCurve
from pyquantlib.market.volatility import BlackConstantVol
from pyquantlib.math.black import black_formula
from pyquantlib.time.date import advance_date


@dataclass(frozen=True)
class CdsResult:
    value: float
    coupon_leg_npv: float
    default_leg_npv: float
    upfront_npv: float
    fair_spread: float
    coupon_leg_bps: float


@dataclass(frozen=True)
class MidPointCdsEngine:
    default_curve: DefaultProbabilityCurve
    recovery_rate: float
    discount_curve: YieldCurve

    def calculate(self, cds: CreditDefaultSwap) -> CdsResult:
        coupon_leg = 0.0
        default_leg = 0.0
        risky_annuity = 0.0
        today = self.discount_curve.reference_date
        dates = cds.schedule.dates
        for start, end in zip(dates[:-1], dates[1:]):
            if end <= today:
                continue
            effective_start = today if start <= today <= end else start
            mid = date.fromordinal((effective_start.toordinal() + end.toordinal()) // 2)
            tau = cds.day_counter.year_fraction(start, end)
            accrued_tau = cds.day_counter.year_fraction(start, mid)
            survival = self.default_curve.survival_probability(end)
            default_probability = self.default_curve.default_probability(effective_start, end)
            df_pay = self.discount_curve.discount(end)
            df_default = self.discount_curve.discount(mid if cds.pays_at_default_time else end)
            risky_annuity += survival * tau * df_pay
            coupon_leg += survival * cds.notional * cds.running_spread * tau * df_pay
            if cds.settles_accrual:
                accrual = accrued_tau if cds.pays_at_default_time else tau
                coupon_leg += default_probability * cds.notional * cds.running_spread * accrual * df_default
            default_leg += default_probability * cds.notional * (1.0 - self.recovery_rate) * df_default

        upfront_npv = cds.upfront * cds.notional * self.discount_curve.discount(dates[0]) if cds.upfront else 0.0
        if cds.side == ProtectionSide.BUYER:
            value = default_leg - coupon_leg - upfront_npv
            signed_coupon = -coupon_leg
            signed_default = default_leg
            signed_upfront = -upfront_npv
        else:
            value = coupon_leg + upfront_npv - default_leg
            signed_coupon = coupon_leg
            signed_default = -default_leg
            signed_upfront = upfront_npv
        fair_spread = 0.0 if risky_annuity == 0.0 else default_leg / (cds.notional * risky_annuity)
        coupon_leg_bps = signed_coupon * 1.0e-4 / cds.running_spread if cds.running_spread else 0.0
        return CdsResult(value, signed_coupon, signed_default, signed_upfront, fair_spread, coupon_leg_bps)


@dataclass(frozen=True)
class BlackCdsOptionEngine:
    default_curve: DefaultProbabilityCurve
    recovery_rate: float
    discount_curve: YieldCurve
    volatility: BlackConstantVol

    def calculate(self, option: CdsOption) -> CdsResult:
        cds_result = MidPointCdsEngine(self.default_curve, self.recovery_rate, self.discount_curve).calculate(option.cds)
        annuity = abs(cds_result.coupon_leg_bps) / 1.0e-4
        expiry = option.expiry_date
        forward_spread = cds_result.fair_spread
        variance = self.volatility.black_variance(expiry, option.strike_spread)
        sign = 1 if option.normalized_option_type == "CALL" else -1
        notional_scale = (option.notional or option.cds.notional) / option.cds.notional
        value = black_formula(sign, forward_spread, option.strike_spread, math.sqrt(max(variance, 0.0)), annuity).value * notional_scale
        return CdsResult(value, 0.0, 0.0, 0.0, forward_spread, 0.0)
