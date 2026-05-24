from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from pyquantlib.instruments.capfloor import CapFloor, CapFloorType
from pyquantlib.market.curves import YieldCurve
from pyquantlib.market.volatility import BlackConstantVol
from pyquantlib.math.black import black_formula


@dataclass(frozen=True)
class CapFloorResult:
    value: float
    vega: float
    optionlet_prices: tuple[float, ...]
    optionlet_vegas: tuple[float, ...]
    optionlet_discount_factors: tuple[float, ...]
    optionlet_atm_forwards: tuple[float, ...]
    optionlet_stddevs: tuple[float, ...]


@dataclass(frozen=True)
class BlackCapFloorEngine:
    discount_curve: YieldCurve
    volatility: BlackConstantVol
    displacement: float = 0.0

    def calculate(self, capfloor: CapFloor) -> CapFloorResult:
        value = 0.0
        vega = 0.0
        prices: list[float] = []
        vegas: list[float] = []
        discounts: list[float] = []
        forwards: list[float] = []
        stddevs: list[float] = []
        today = self.volatility.reference_date
        settlement = self.discount_curve.reference_date

        for i, coupon in enumerate(capfloor.floating_leg):
            price = 0.0
            optionlet_vega = 0.0
            stddev = 0.0
            discount = 0.0
            forward = 0.0
            if coupon.payment_date > settlement:
                discount = self.discount_curve.discount(coupon.payment_date)
                forward = coupon.index.fixing(coupon.fixing_date, coupon.accrual_start_date, coupon.accrual_end_date)
                accrual_factor = coupon.nominal * coupon.gearing * coupon.accrual_period
                discounted_accrual = discount * accrual_factor
                sqrt_time = 0.0
                if coupon.fixing_date > today:
                    sqrt_time = math.sqrt(max(self.volatility.time_from_reference(coupon.fixing_date), 0.0))

                if capfloor.type in (CapFloorType.CAP, CapFloorType.COLLAR):
                    strike = (capfloor.cap_rates[i] - coupon.spread) / coupon.gearing
                    stddev = math.sqrt(max(self.volatility.black_variance(coupon.fixing_date, strike), 0.0)) if sqrt_time > 0.0 else 0.0
                    black = black_formula(1, forward, strike, stddev, discounted_accrual, self.displacement)
                    price = black.value
                    optionlet_vega = black.vega_by_stddev * sqrt_time

                if capfloor.type in (CapFloorType.FLOOR, CapFloorType.COLLAR):
                    strike = (capfloor.floor_rates[i] - coupon.spread) / coupon.gearing
                    floor_stddev = math.sqrt(max(self.volatility.black_variance(coupon.fixing_date, strike), 0.0)) if sqrt_time > 0.0 else 0.0
                    black = black_formula(-1, forward, strike, floor_stddev, discounted_accrual, self.displacement)
                    floorlet = black.value
                    floorlet_vega = black.vega_by_stddev * sqrt_time
                    if capfloor.type == CapFloorType.FLOOR:
                        price = floorlet
                        optionlet_vega = floorlet_vega
                        stddev = floor_stddev
                    else:
                        price -= floorlet
                        optionlet_vega -= floorlet_vega

                value += price
                vega += optionlet_vega

            prices.append(price)
            vegas.append(optionlet_vega)
            discounts.append(discount)
            forwards.append(forward)
            stddevs.append(stddev)

        return CapFloorResult(
            value,
            vega,
            tuple(prices),
            tuple(vegas),
            tuple(discounts),
            tuple(forwards),
            tuple(stddevs),
        )
