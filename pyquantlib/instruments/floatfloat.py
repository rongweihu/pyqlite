from __future__ import annotations

from dataclasses import dataclass

from pyquantlib.cashflows.cashflow import CashFlow
from pyquantlib.cashflows.legs import ibor_leg
from pyquantlib.indexes.ibor import IborIndex
from pyquantlib.instruments.swap import SwapType
from pyquantlib.time.calendar import BusinessDayConvention
from pyquantlib.time.daycounter import DayCounter
from pyquantlib.time.schedule import Schedule


@dataclass(frozen=True)
class FloatFloatSwap:
    swap_type: SwapType
    nominal1: tuple[float, ...]
    nominal2: tuple[float, ...]
    schedule1: Schedule
    index1: IborIndex
    day_count1: DayCounter
    schedule2: Schedule
    index2: IborIndex
    day_count2: DayCounter
    intermediate_capital_exchange: bool = False
    final_capital_exchange: bool = False
    gearing1: tuple[float, ...] = ()
    spread1: tuple[float, ...] = ()
    gearing2: tuple[float, ...] = ()
    spread2: tuple[float, ...] = ()
    payment_convention1: BusinessDayConvention = BusinessDayConvention.FOLLOWING
    payment_convention2: BusinessDayConvention = BusinessDayConvention.FOLLOWING

    def __post_init__(self) -> None:
        _validate_size(self.nominal1, len(self.schedule1.dates) - 1, "nominal1")
        _validate_size(self.nominal2, len(self.schedule2.dates) - 1, "nominal2")
        object.__setattr__(self, "gearing1", _default(self.gearing1, len(self.nominal1), 1.0, "gearing1"))
        object.__setattr__(self, "gearing2", _default(self.gearing2, len(self.nominal2), 1.0, "gearing2"))
        object.__setattr__(self, "spread1", _default(self.spread1, len(self.nominal1), 0.0, "spread1"))
        object.__setattr__(self, "spread2", _default(self.spread2, len(self.nominal2), 0.0, "spread2"))

    @classmethod
    def from_nominals(
        cls,
        swap_type: SwapType,
        nominal1: float,
        nominal2: float,
        schedule1: Schedule,
        index1: IborIndex,
        day_count1: DayCounter,
        schedule2: Schedule,
        index2: IborIndex,
        day_count2: DayCounter,
        spread1: float = 0.0,
        spread2: float = 0.0,
    ) -> "FloatFloatSwap":
        n1 = len(schedule1.dates) - 1
        n2 = len(schedule2.dates) - 1
        return cls(
            swap_type,
            (nominal1,) * n1,
            (nominal2,) * n2,
            schedule1,
            index1,
            day_count1,
            schedule2,
            index2,
            day_count2,
            spread1=(spread1,) * n1,
            spread2=(spread2,) * n2,
        )

    @property
    def leg1(self) -> list:
        leg = ibor_leg(
            self.schedule1,
            self.nominal1,
            self.index1,
            self.spread1,
            self.day_count1,
            payment_convention=self.payment_convention1,
            gearing=self.gearing1,
        )
        return _with_capital_exchanges(leg, self.nominal1, self.intermediate_capital_exchange, self.final_capital_exchange)

    @property
    def leg2(self) -> list:
        leg = ibor_leg(
            self.schedule2,
            self.nominal2,
            self.index2,
            self.spread2,
            self.day_count2,
            payment_convention=self.payment_convention2,
            gearing=self.gearing2,
        )
        return _with_capital_exchanges(leg, self.nominal2, self.intermediate_capital_exchange, self.final_capital_exchange)

    @property
    def legs(self) -> list[list]:
        return [self.leg1, self.leg2]

    @property
    def payer_signs(self) -> list[float]:
        if self.swap_type == SwapType.PAYER:
            return [-1.0, 1.0]
        return [1.0, -1.0]


def _with_capital_exchanges(leg: list, notionals: tuple[float, ...], intermediate: bool, final: bool) -> list:
    result = list(leg)
    offset = 0
    if intermediate:
        for i in range(len(notionals) - 1):
            redemption = notionals[i] - notionals[i + 1]
            if redemption != 0.0:
                result.insert(i + 1 + offset, CashFlow(leg[i].payment_date, redemption))
                offset += 1
    if final:
        result.append(CashFlow(leg[-1].payment_date, notionals[-1]))
    return result


def _default(values: tuple[float, ...], length: int, default: float, name: str) -> tuple[float, ...]:
    if not values:
        return (default,) * length
    _validate_size(values, length, name)
    return values


def _validate_size(values: tuple[float, ...], length: int, name: str) -> None:
    if len(values) != length:
        raise ValueError(f"{name} size ({len(values)}) must match schedule periods ({length})")
