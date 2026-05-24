from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PricingResult:
    value: float
    fair_value: float = 0.0
    leg1_npv: float = 0.0
    leg2_npv: float = 0.0
