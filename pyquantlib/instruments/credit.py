from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pyquantlib.time.calendar import BusinessDayConvention
from pyquantlib.time.daycounter import DayCounter
from pyquantlib.time.schedule import Schedule


class ProtectionSide(Enum):
    BUYER = "Buyer"
    SELLER = "Seller"


@dataclass(frozen=True)
class CreditDefaultSwap:
    side: ProtectionSide
    notional: float
    running_spread: float
    schedule: Schedule
    day_counter: DayCounter
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING
    settles_accrual: bool = True
    pays_at_default_time: bool = True
    upfront: float = 0.0

    @property
    def protection_start_date(self):
        return self.schedule.dates[0]

    @property
    def protection_end_date(self):
        return self.schedule.dates[-1]


@dataclass(frozen=True)
class CdsOption:
    option_type: str
    expiry_date: object
    strike_spread: float
    cds: CreditDefaultSwap
    notional: float | None = None

    @property
    def normalized_option_type(self) -> str:
        value = self.option_type.strip().upper()
        if value not in ("CALL", "PUT", "C", "P"):
            raise ValueError("option_type must be CALL or PUT")
        return "CALL" if value in ("CALL", "C") else "PUT"
