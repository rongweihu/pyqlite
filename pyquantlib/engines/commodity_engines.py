from __future__ import annotations

import math
from dataclasses import dataclass

from pyquantlib.engines.pricing_result import PricingResult
from pyquantlib.instruments.commodity import CommodityForward, CommodityOption, CommoditySwap
from pyquantlib.instruments.fra import PositionType
from pyquantlib.instruments.fx_option import OptionType
from pyquantlib.instruments.swap import SwapType
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.quote import SimpleQuote
from pyquantlib.market.volatility import BlackConstantVol
from pyquantlib.math.black import black_formula


@dataclass(frozen=True)
class DiscountingCommodityForwardEngine:
    forward_curve: YieldCurve
    discount_curve: YieldCurve
    spot: SimpleQuote

    def forward_price(self, maturity) -> float:
        return self.spot.value / self.forward_curve.discount(maturity)

    def calculate(self, forward: CommodityForward) -> PricingResult:
        fair = self.forward_price(forward.maturity_date)
        sign = 1.0 if forward.position == PositionType.LONG else -1.0
        value = sign * forward.quantity * (fair - forward.contract_price) * self.discount_curve.discount(forward.maturity_date)
        return PricingResult(value, fair)


@dataclass(frozen=True)
class DiscountingCommoditySwapEngine:
    forward_curve: YieldCurve
    discount_curve: YieldCurve
    spot: SimpleQuote

    def forward_price(self, fixing_date) -> float:
        return self.spot.value / self.forward_curve.discount(fixing_date)

    def calculate(self, swap: CommoditySwap) -> PricingResult:
        floating = 0.0
        fixed = 0.0
        annuity = 0.0
        for payment_date in swap.schedule.dates[1:]:
            df = self.discount_curve.discount(payment_date)
            annuity += swap.quantity * df
            floating += swap.quantity * self.forward_price(payment_date) * df
            fixed += swap.quantity * swap.fixed_price * df
        sign = 1.0 if swap.swap_type == SwapType.RECEIVER else -1.0
        fair = 0.0 if annuity == 0.0 else floating / annuity
        return PricingResult(sign * (floating - fixed), fair, sign * floating, -sign * fixed)


@dataclass(frozen=True)
class AnalyticCommodityOptionEngine:
    forward_curve: YieldCurve
    discount_curve: YieldCurve
    volatility: BlackConstantVol
    spot: SimpleQuote

    def calculate(self, option: CommodityOption) -> PricingResult:
        forward = self.spot.value / self.forward_curve.discount(option.expiry_date)
        variance = self.volatility.black_variance(option.expiry_date, option.strike)
        sign = 1 if option.option_type == OptionType.CALL else -1
        value = option.quantity * black_formula(sign, forward, option.strike, math.sqrt(max(variance, 0.0)), self.discount_curve.discount(option.expiry_date)).value
        return PricingResult(value, forward)
