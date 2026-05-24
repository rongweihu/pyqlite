from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pyquantlib.cashflows.cashflow import IborCoupon


class CapFloorType(Enum):
    CAP = "Cap"
    FLOOR = "Floor"
    COLLAR = "Collar"


@dataclass(frozen=True)
class CapFloor:
    type: CapFloorType
    floating_leg: tuple[IborCoupon, ...]
    cap_rates: tuple[float, ...] = ()
    floor_rates: tuple[float, ...] = ()

    @classmethod
    def cap(cls, floating_leg: list[IborCoupon] | tuple[IborCoupon, ...], strikes: tuple[float, ...]) -> "CapFloor":
        return cls(CapFloorType.CAP, tuple(floating_leg), cap_rates=strikes)

    @classmethod
    def floor(cls, floating_leg: list[IborCoupon] | tuple[IborCoupon, ...], strikes: tuple[float, ...]) -> "CapFloor":
        return cls(CapFloorType.FLOOR, tuple(floating_leg), floor_rates=strikes)

    @classmethod
    def collar(
        cls,
        floating_leg: list[IborCoupon] | tuple[IborCoupon, ...],
        cap_rates: tuple[float, ...],
        floor_rates: tuple[float, ...],
    ) -> "CapFloor":
        return cls(CapFloorType.COLLAR, tuple(floating_leg), cap_rates, floor_rates)

    def __post_init__(self) -> None:
        if not self.floating_leg:
            raise ValueError("no floating leg given")
        if self.type in (CapFloorType.CAP, CapFloorType.COLLAR) and not self.cap_rates:
            raise ValueError("no cap rates given")
        if self.type in (CapFloorType.FLOOR, CapFloorType.COLLAR) and not self.floor_rates:
            raise ValueError("no floor rates given")
        object.__setattr__(self, "cap_rates", _extend(self.cap_rates, len(self.floating_leg)))
        object.__setattr__(self, "floor_rates", _extend(self.floor_rates, len(self.floating_leg)))


def _extend(values: tuple[float, ...], length: int) -> tuple[float, ...]:
    if not values:
        return values
    if len(values) >= length:
        return values
    return values + (values[-1],) * (length - len(values))
