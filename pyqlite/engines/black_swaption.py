from __future__ import annotations

import math
from dataclasses import dataclass

from pyqlite.engines.discounting_swap import DiscountingSwapEngine
from pyqlite.instruments.swap import SwapType
from pyqlite.instruments.swaption import SettlementType, Swaption
from pyqlite.market.curves import YieldCurve
from pyqlite.math.black import black_formula
from pyqlite.time.daycounter import Actual365Fixed


@dataclass(frozen=True)
class SwaptionResult:
    value: float
    annuity: float
    atm_forward: float
    strike: float
    stddev: float
    vega: float
    delta: float
    time_to_expiry: float
    forward_price: float


@dataclass(frozen=True)
class BlackSwaptionEngine:
    discount_curve: YieldCurve
    volatility: object
    displacement: float = 0.0

    def calculate(self, swaption: Swaption) -> SwaptionResult:
        if swaption.settlement_type != SettlementType.PHYSICAL:
            raise ValueError("only physical settlement is supported")
        swap = swaption.swap
        if swap.fixed_leg[0].accrual_start_date < swaption.exercise_date:
            raise ValueError("swap start before exercise date is not supported")

        swap_result = DiscountingSwapEngine(self.discount_curve, include_settlement_date_flows=False).calculate(swap)
        strike = swap.fixed_rate
        atm_forward = swap_result.fair_rate
        spread = swap.spread
        if spread != 0.0:
            correction = spread * abs(swap_result.floating_leg_bps / swap_result.fixed_leg_bps)
            strike -= correction
            atm_forward -= correction

        annuity = abs(swap_result.fixed_leg_bps) / 1.0e-4
        swap_length = Actual365Fixed().year_fraction(
            swap.fixed_leg[0].accrual_start_date,
            swap.fixed_leg[-1].accrual_end_date,
        )
        variance = _black_variance(self.volatility, swaption.exercise_date, swap_length, strike, atm_forward)
        stddev = math.sqrt(max(variance, 0.0))
        option_sign = 1 if swap.swap_type == SwapType.PAYER else -1
        displacement = self.displacement + _shift(self.volatility, swaption.exercise_date, swap_length)
        black = black_formula(option_sign, atm_forward, strike, stddev, annuity, displacement)
        exercise_time = max(self.volatility.time_from_reference(swaption.exercise_date), 0.0)
        vega = black.vega_by_stddev * math.sqrt(exercise_time)
        exercise_discount = self.discount_curve.discount(swaption.exercise_date)
        return SwaptionResult(
            value=black.value,
            annuity=annuity,
            atm_forward=atm_forward,
            strike=strike,
            stddev=stddev,
            vega=vega,
            delta=black.forward_delta,
            time_to_expiry=exercise_time,
            forward_price=black.value / exercise_discount,
        )


def _black_variance(volatility: object, exercise_date, swap_length: float, strike: float, atm_forward: float) -> float:
    try:
        return volatility.black_variance(exercise_date, swap_length, strike, atm_forward)
    except TypeError:
        try:
            return volatility.black_variance(exercise_date, swap_length, strike)
        except TypeError:
            return volatility.black_variance(exercise_date, strike)


def _shift(volatility: object, exercise_date, swap_length: float) -> float:
    shift = getattr(volatility, "shift", None)
    if shift is None:
        return 0.0
    try:
        return shift(exercise_date, swap_length)
    except TypeError:
        return shift(exercise_date)
