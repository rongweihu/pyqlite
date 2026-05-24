from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.cashflows.analytics import leg_npv
from pyquantlib.instruments.bond import Bond
from pyquantlib.market.curves import YieldCurve


@dataclass(frozen=True)
class BondResult:
    value: float
    settlement_value: float
    valuation_date: date
    settlement_date: date


@dataclass(frozen=True)
class DiscountingBondEngine:
    discount_curve: YieldCurve
    include_settlement_date_flows: bool = False

    def calculate(self, bond: Bond, evaluation_date: date | None = None) -> BondResult:
        valuation_date = evaluation_date or self.discount_curve.reference_date
        settlement_date = bond.settlement_date(valuation_date)
        value = leg_npv(
            list(bond.cashflows),
            self.discount_curve,
            valuation_date,
            valuation_date,
            self.include_settlement_date_flows,
        )
        settlement_value = leg_npv(
            list(bond.cashflows),
            self.discount_curve,
            settlement_date,
            settlement_date,
            False,
        )
        return BondResult(value, settlement_value, valuation_date, settlement_date)
