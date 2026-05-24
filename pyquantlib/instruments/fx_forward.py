from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyquantlib.time.calendar import BusinessDayConvention, Calendar, NullCalendar


@dataclass(frozen=True)
class FxForward:
    source_nominal: float
    source_currency: str
    target_nominal: float
    target_currency: str
    maturity_date: date
    pay_source_currency: bool
    settlement_days: int = 2
    settlement_calendar: Calendar = NullCalendar()

    def __post_init__(self) -> None:
        if not self.source_currency:
            raise ValueError("source currency must not be empty")
        if not self.target_currency:
            raise ValueError("target currency must not be empty")
        if self.source_currency == self.target_currency:
            raise ValueError("source and target currencies must be different")
        if self.source_nominal <= 0.0:
            raise ValueError("source nominal must be positive")
        if self.target_nominal <= 0.0:
            raise ValueError("target nominal must be positive")

    @classmethod
    def from_forward_rate(
        cls,
        source_nominal: float,
        source_currency: str,
        target_currency: str,
        forward_rate: float,
        maturity_date: date,
        pay_source_currency: bool,
        settlement_days: int = 2,
        settlement_calendar: Calendar = NullCalendar(),
    ) -> "FxForward":
        return cls(
            source_nominal,
            source_currency,
            source_nominal * forward_rate,
            target_currency,
            maturity_date,
            pay_source_currency,
            settlement_days,
            settlement_calendar,
        )

    @property
    def forward_rate(self) -> float:
        return self.target_nominal / self.source_nominal

    def settlement_date(self, evaluation_date: date) -> date:
        return self.settlement_calendar.advance(
            evaluation_date,
            self.settlement_days,
            BusinessDayConvention.FOLLOWING,
        )
