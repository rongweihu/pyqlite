from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.instruments.fra import ForwardRateAgreement
from pyquantlib.market.curves import YieldCurve


@dataclass(frozen=True)
class FraResult:
    value: float
    amount: float
    forward_rate: float
    strike_forward_rate: float
    accrual_time: float
    discount_factor: float


@dataclass(frozen=True)
class DiscountingFraEngine:
    discount_curve: YieldCurve | None = None

    def calculate(self, fra: ForwardRateAgreement, evaluation_date: date | None = None) -> FraResult:
        curve = self.discount_curve or fra.index.forwarding_curve
        if curve is None:
            raise ValueError("FRA requires a discount curve or an index forwarding curve")
        evaluation_date = evaluation_date or curve.reference_date
        forward_curve = fra.index.forwarding_curve
        if forward_curve is None:
            raise ValueError("FRA index requires a forwarding curve")

        forward_rate = fra.index.fixing(fra.fixing_date, fra.value_date, fra.maturity_date)
        tau = fra.index.day_counter.year_fraction(fra.value_date, fra.maturity_date)
        if tau <= 0.0:
            raise ValueError("invalid FRA accrual period")
        amount = fra.notional * fra.position.value * (forward_rate - fra.strike_forward_rate) * tau / (1.0 + forward_rate * tau)
        discount = curve.discount(fra.value_date)
        value = 0.0 if fra.value_date <= evaluation_date else amount * discount
        return FraResult(
            value=value,
            amount=amount,
            forward_rate=forward_rate,
            strike_forward_rate=fra.strike_forward_rate,
            accrual_time=tau,
            discount_factor=discount,
        )
