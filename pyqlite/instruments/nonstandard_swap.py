from __future__ import annotations

from dataclasses import dataclass

from pyqlite.cashflows.cashflow import CashFlow
from pyqlite.cashflows.legs import fixed_rate_leg, ibor_leg
from pyqlite.indexes.ibor import IborIndex
from pyqlite.instruments.swap import SwapType
from pyqlite.time.calendar import BusinessDayConvention
from pyqlite.time.daycounter import DayCounter
from pyqlite.time.schedule import Schedule


@dataclass(frozen=True)
class NonstandardSwap:
    swap_type: SwapType
    fixed_nominal: tuple[float, ...]
    floating_nominal: tuple[float, ...]
    fixed_schedule: Schedule
    fixed_rate: tuple[float, ...]
    fixed_day_counter: DayCounter
    floating_schedule: Schedule
    ibor_index: IborIndex
    gearing: tuple[float, ...]
    spread: tuple[float, ...]
    floating_day_counter: DayCounter
    intermediate_capital_exchange: bool = False
    final_capital_exchange: bool = False
    payment_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING

    def __post_init__(self) -> None:
        _validate_size(self.fixed_nominal, len(self.fixed_schedule.dates) - 1, "fixed_nominal")
        _validate_size(self.fixed_rate, len(self.fixed_nominal), "fixed_rate")
        _validate_size(self.floating_nominal, len(self.floating_schedule.dates) - 1, "floating_nominal")
        _validate_size(self.gearing, len(self.floating_nominal), "gearing")
        _validate_size(self.spread, len(self.floating_nominal), "spread")

    @property
    def fixed_leg(self) -> list:
        leg = fixed_rate_leg(
            self.fixed_schedule,
            self.fixed_nominal,
            self.fixed_rate,
            self.fixed_day_counter,
            payment_convention=self.payment_convention,
        )
        return _with_capital_exchanges(leg, self.fixed_nominal, self.intermediate_capital_exchange, self.final_capital_exchange)

    @property
    def floating_leg(self) -> list:
        leg = ibor_leg(
            self.floating_schedule,
            self.floating_nominal,
            self.ibor_index,
            self.spread,
            self.floating_day_counter,
            payment_convention=self.payment_convention,
            gearing=self.gearing,
        )
        return _with_capital_exchanges(leg, self.floating_nominal, self.intermediate_capital_exchange, self.final_capital_exchange)

    @property
    def legs(self) -> list[list]:
        return [self.fixed_leg, self.floating_leg]

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


def _validate_size(values: tuple[float, ...], length: int, name: str) -> None:
    if len(values) != length:
        raise ValueError(f"{name} size ({len(values)}) must match expected size ({length})")
