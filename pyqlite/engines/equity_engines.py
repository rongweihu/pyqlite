from __future__ import annotations

import math
from dataclasses import dataclass

from pyqlite.engines.pricing_result import PricingResult
from pyqlite.instruments.equity import EquityOption, EquityTotalReturnSwap
from pyqlite.instruments.fx_option import OptionType
from pyqlite.instruments.swap import SwapType
from pyqlite.market.curves import YieldCurve
from pyqlite.market.quote import SimpleQuote
from pyqlite.market.volatility import BlackConstantVol
from pyqlite.math.black import black_formula


@dataclass(frozen=True)
class AnalyticEquityOptionEngine:
    spot: SimpleQuote
    dividend_curve: YieldCurve
    risk_free_curve: YieldCurve
    volatility: BlackConstantVol

    def calculate(self, option: EquityOption) -> PricingResult:
        expiry = option.expiry_date
        risk_free_df = self.risk_free_curve.discount(expiry)
        dividend_df = self.dividend_curve.discount(expiry)
        forward = self.spot.value * dividend_df / risk_free_df
        variance = self.volatility.black_variance(expiry, option.strike)
        sign = 1 if option.option_type == OptionType.CALL else -1
        value = option.quantity * black_formula(sign, forward, option.strike, math.sqrt(max(variance, 0.0)), risk_free_df).value
        return PricingResult(value, forward)


@dataclass(frozen=True)
class DiscountingEquityTotalReturnSwapEngine:
    spot: SimpleQuote
    dividend_curve: YieldCurve
    funding_curve: YieldCurve
    discount_curve: YieldCurve

    def calculate(self, swap: EquityTotalReturnSwap) -> PricingResult:
        maturity = swap.maturity_date
        equity_forward = self.spot.value * self.dividend_curve.discount(maturity) / self.discount_curve.discount(maturity)
        equity_leg_npv = swap.notional * (equity_forward / swap.initial_price - 1.0) * self.discount_curve.discount(maturity)
        ex_margin_interest_leg_npv = 0.0
        margin_bps = 0.0
        for start, end in zip(swap.funding_schedule.dates[:-1], swap.funding_schedule.dates[1:]):
            tau = swap.funding_day_counter.year_fraction(start, end)
            df = self.discount_curve.discount(end)
            rate = self.funding_curve.forward_rate(start, end)
            ex_margin_interest_leg_npv += swap.notional * swap.funding_gearing * rate * tau * df
            margin_bps += swap.notional * tau * df * 1.0e-4
        margin_leg_npv = swap.funding_spread * margin_bps / 1.0e-4
        interest_leg_npv = ex_margin_interest_leg_npv + margin_leg_npv
        equity_sign = 1.0 if swap.swap_type == SwapType.RECEIVER else -1.0
        interest_sign = -equity_sign
        value = equity_sign * equity_leg_npv + interest_sign * interest_leg_npv
        fair_margin = 0.0
        if margin_bps != 0.0:
            interest_leg_bps = interest_sign * margin_bps
            ex_margin_signed_interest = interest_sign * ex_margin_interest_leg_npv
            fair_margin = -(equity_sign * equity_leg_npv + ex_margin_signed_interest) / (interest_leg_bps / 1.0e-4)
        return PricingResult(value, fair_margin, equity_sign * equity_leg_npv, interest_sign * interest_leg_npv)
