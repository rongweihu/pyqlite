from __future__ import annotations

from dataclasses import dataclass

from pyquantlib.cashflows.analytics import leg_npv_bps
from pyquantlib.cashflows.cashflow import CashFlow
from pyquantlib.cashflows.legs import fixed_rate_leg, ibor_leg
from pyquantlib.instruments.swap import SwapType
from pyquantlib.instruments.xccy import CrossCurrencyBasisSwap, CrossCurrencyFixedFloatSwap
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.quote import SimpleQuote


@dataclass(frozen=True)
class XccyBasisSwapResult:
    value: float
    pay_leg_npv: float
    receive_leg_npv: float
    pay_leg_bps: float
    receive_leg_bps: float
    fair_pay_spread: float
    fair_receive_spread: float


@dataclass(frozen=True)
class XccyFixedFloatSwapResult:
    value: float
    fixed_leg_npv: float
    float_leg_npv: float
    fixed_leg_bps: float
    float_leg_bps: float
    fair_fixed_rate: float
    fair_float_spread: float


@dataclass(frozen=True)
class DiscountingCrossCurrencySwapEngine:
    domestic_currency: str
    domestic_curve: YieldCurve
    foreign_currency: str
    foreign_curve: YieldCurve
    spot_fx: SimpleQuote

    def calculate_basis_swap(self, swap: CrossCurrencyBasisSwap) -> XccyBasisSwapResult:
        pay_leg = ibor_leg(swap.pay_schedule, swap.pay_nominal, swap.pay_index, swap.pay_spread, gearing=swap.pay_gearing)
        rec_leg = ibor_leg(swap.receive_schedule, swap.receive_nominal, swap.receive_index, swap.receive_spread, gearing=swap.receive_gearing)
        if swap.exchange_notionals:
            pay_leg = _with_notional_exchanges(pay_leg, swap.pay_nominal, -1.0)
            rec_leg = _with_notional_exchanges(rec_leg, swap.receive_nominal, 1.0)
        pay_npv, pay_bps = self._leg_value(pay_leg, swap.pay_currency, -1.0)
        rec_npv, rec_bps = self._leg_value(rec_leg, swap.receive_currency, 1.0)
        value = pay_npv + rec_npv
        fair_pay_spread = swap.pay_spread - value / pay_bps * 1.0e-4 if pay_bps else 0.0
        fair_receive_spread = swap.receive_spread - value / rec_bps * 1.0e-4 if rec_bps else 0.0
        return XccyBasisSwapResult(value, pay_npv, rec_npv, pay_bps, rec_bps, fair_pay_spread, fair_receive_spread)

    def calculate_fixed_float_swap(self, swap: CrossCurrencyFixedFloatSwap) -> XccyFixedFloatSwapResult:
        fixed_leg = fixed_rate_leg(swap.fixed_schedule, swap.fixed_nominal, swap.fixed_rate, swap.fixed_day_counter)
        float_leg = ibor_leg(swap.float_schedule, swap.float_nominal, swap.float_index, swap.float_spread)
        fixed_sign = -1.0 if swap.swap_type == SwapType.PAYER else 1.0
        float_sign = -fixed_sign
        if swap.exchange_notionals:
            fixed_leg = _with_notional_exchanges(fixed_leg, swap.fixed_nominal, fixed_sign)
            float_leg = _with_notional_exchanges(float_leg, swap.float_nominal, float_sign)
        fixed_npv, fixed_bps = self._leg_value(fixed_leg, swap.fixed_currency, fixed_sign)
        float_npv, float_bps = self._leg_value(float_leg, swap.float_currency, float_sign)
        value = fixed_npv + float_npv
        fair_rate = swap.fixed_rate - value / fixed_bps * 1.0e-4 if fixed_bps else 0.0
        fair_spread = swap.float_spread - value / float_bps * 1.0e-4 if float_bps else 0.0
        return XccyFixedFloatSwapResult(value, fixed_npv, float_npv, fixed_bps, float_bps, fair_rate, fair_spread)

    def _leg_value(self, leg: list, currency: str, sign: float) -> tuple[float, float]:
        curve = self.domestic_curve if currency == self.domestic_currency else self.foreign_curve
        npv, bps = leg_npv_bps(leg, curve, curve.reference_date, curve.reference_date, False)
        fx = 1.0 if currency == self.domestic_currency else self.spot_fx.value
        return sign * npv * fx, sign * bps * fx


def _with_notional_exchanges(leg: list, nominal: float, first_sign: float) -> list:
    if not leg:
        return leg
    return [CashFlow(leg[0].accrual_start_date, first_sign * nominal)] + list(leg) + [CashFlow(leg[-1].payment_date, -first_sign * nominal)]
