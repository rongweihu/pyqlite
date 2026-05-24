from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.instruments.fx_forward import FxForward
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.quote import SimpleQuote


@dataclass(frozen=True)
class FxForwardResult:
    value: float
    npv_source_currency: float
    npv_target_currency: float
    fair_forward_rate: float
    zero_npv_forward_rate: float
    source_discount_factor: float
    target_discount_factor: float


@dataclass(frozen=True)
class DiscountingFxForwardEngine:
    source_currency_discount_curve: YieldCurve
    target_currency_discount_curve: YieldCurve
    spot_fx: SimpleQuote

    def calculate(self, forward: FxForward, evaluation_date: date | None = None) -> FxForwardResult:
        evaluation_date = evaluation_date or self.source_currency_discount_curve.reference_date
        settlement_date = forward.settlement_date(evaluation_date)
        spot = self.spot_fx.value
        if spot <= 0.0:
            raise ValueError("spot FX rate must be positive")
        df_source = self.source_currency_discount_curve.discount(
            forward.maturity_date
        ) / self.source_currency_discount_curve.discount(settlement_date)
        df_target = self.target_currency_discount_curve.discount(
            forward.maturity_date
        ) / self.target_currency_discount_curve.discount(settlement_date)
        fair_forward = spot * df_target / df_source
        zero_npv_forward = spot * df_source / df_target
        pv_source = forward.source_nominal * df_source
        pv_target = forward.target_nominal * df_target
        pv_target_in_source = pv_target / spot
        if forward.pay_source_currency:
            npv_source = -pv_source + pv_target_in_source
        else:
            npv_source = pv_source - pv_target_in_source
        return FxForwardResult(
            value=npv_source,
            npv_source_currency=npv_source,
            npv_target_currency=npv_source * spot,
            fair_forward_rate=fair_forward,
            zero_npv_forward_rate=zero_npv_forward,
            source_discount_factor=df_source,
            target_discount_factor=df_target,
        )
