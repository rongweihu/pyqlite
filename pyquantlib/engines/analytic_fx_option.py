from __future__ import annotations

import math
from dataclasses import dataclass

from pyquantlib.instruments.fx_option import FxOption
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.quote import SimpleQuote
from pyquantlib.market.volatility import BlackConstantVol
from pyquantlib.math.black import black_formula


@dataclass(frozen=True)
class FxOptionResult:
    value: float
    delta_spot: float
    gamma_spot: float
    vega: float
    forward: float
    domestic_discount: float
    foreign_discount: float
    stddev: float


@dataclass(frozen=True)
class AnalyticFxOptionEngine:
    spot_fx: SimpleQuote
    domestic_curve: YieldCurve
    foreign_curve: YieldCurve
    volatility: BlackConstantVol

    def calculate(self, option: FxOption) -> FxOptionResult:
        spot = self.spot_fx.value
        if spot <= 0.0:
            raise ValueError("spot FX rate must be positive")
        domestic_df = self.domestic_curve.discount(option.expiry_date)
        foreign_df = self.foreign_curve.discount(option.expiry_date)
        forward = spot * foreign_df / domestic_df
        variance = self.volatility.black_variance(option.expiry_date, option.strike)
        stddev = math.sqrt(max(variance, 0.0))
        black = black_formula(option.sign, forward, option.strike, stddev, domestic_df)
        t = max(self.volatility.time_from_reference(option.expiry_date), 0.0)
        delta_spot = option.foreign_notional * black.forward_delta * foreign_df / domestic_df
        gamma_spot = 0.0
        if stddev > 0.0 and spot > 0.0:
            gamma_spot = option.foreign_notional * foreign_df * math.exp(-0.5 * black.d1 * black.d1) / (spot * stddev * math.sqrt(2.0 * math.pi))
        vega = option.foreign_notional * black.vega_by_stddev * math.sqrt(t)
        return FxOptionResult(
            value=option.foreign_notional * black.value,
            delta_spot=delta_spot,
            gamma_spot=gamma_spot,
            vega=vega,
            forward=forward,
            domestic_discount=domestic_df,
            foreign_discount=foreign_df,
            stddev=stddev,
        )
