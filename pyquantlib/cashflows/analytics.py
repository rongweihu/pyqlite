from __future__ import annotations

from datetime import date

from pyquantlib.market.curves import YieldCurve


def leg_npv(
    leg: list,
    discount_curve: YieldCurve,
    settlement_date: date | None = None,
    npv_date: date | None = None,
    include_settlement_date_flows: bool = False,
) -> float:
    npv, _ = leg_npv_bps(leg, discount_curve, settlement_date, npv_date, include_settlement_date_flows)
    return npv


def leg_bps(
    leg: list,
    discount_curve: YieldCurve,
    settlement_date: date | None = None,
    npv_date: date | None = None,
    include_settlement_date_flows: bool = False,
) -> float:
    _, bps = leg_npv_bps(leg, discount_curve, settlement_date, npv_date, include_settlement_date_flows)
    return bps


def leg_npv_bps(
    leg: list,
    discount_curve: YieldCurve,
    settlement_date: date | None = None,
    npv_date: date | None = None,
    include_settlement_date_flows: bool = False,
) -> tuple[float, float]:
    settlement_date = settlement_date or discount_curve.reference_date
    npv_date = npv_date or discount_curve.reference_date
    npv_discount = discount_curve.discount(npv_date)
    total_npv = 0.0
    total_bps = 0.0
    for cf in leg:
        if _has_occurred(cf.payment_date, settlement_date, include_settlement_date_flows):
            continue
        discount = discount_curve.discount(cf.payment_date) / npv_discount
        total_npv += cf.amount * discount
        if hasattr(cf, "basis_point_value"):
            total_bps += cf.basis_point_value() * discount
    return total_npv, total_bps


def _has_occurred(payment_date: date, settlement_date: date, include_ref_date: bool) -> bool:
    return payment_date < settlement_date or (payment_date == settlement_date and not include_ref_date)
