from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from pyquantlib.math.distributions import inverse_normal_cdf, normal_cdf, normal_pdf


class DeltaType(Enum):
    SPOT = "Spot"
    FWD = "Fwd"
    PA_SPOT = "PaSpot"
    PA_FWD = "PaFwd"


class AtmType(Enum):
    ATM_SPOT = "AtmSpot"
    ATM_FWD = "AtmFwd"
    ATM_DELTA_NEUTRAL = "AtmDeltaNeutral"
    ATM_VEGA_MAX = "AtmVegaMax"
    ATM_GAMMA_MAX = "AtmGammaMax"
    ATM_PUT_CALL_50 = "AtmPutCall50"


@dataclass(frozen=True)
class BlackDeltaCalculator:
    option_sign: int
    delta_type: DeltaType
    spot: float
    domestic_discount: float
    foreign_discount: float
    stddev: float

    def __post_init__(self) -> None:
        if self.option_sign not in (-1, 1):
            raise ValueError("option_sign must be 1 for call or -1 for put")
        if self.spot <= 0.0:
            raise ValueError("positive spot value required")
        if self.domestic_discount <= 0.0 or self.foreign_discount <= 0.0:
            raise ValueError("positive discount factors required")
        if self.stddev < 0.0:
            raise ValueError("non-negative standard deviation required")

    @property
    def forward(self) -> float:
        return self.spot * self.foreign_discount / self.domestic_discount

    def delta_from_strike(self, strike: float) -> float:
        if strike < 0.0:
            raise ValueError("positive strike value required")
        phi = self.option_sign
        if self.delta_type == DeltaType.SPOT:
            return phi * self.foreign_discount * self._cum_d1(strike)
        if self.delta_type == DeltaType.FWD:
            return phi * self._cum_d1(strike)
        if self.delta_type == DeltaType.PA_SPOT:
            return phi * self.foreign_discount * self._cum_d2(strike) * strike / self.forward
        if self.delta_type == DeltaType.PA_FWD:
            return phi * self._cum_d2(strike) * strike / self.forward
        raise ValueError(f"invalid delta type {self.delta_type}")

    def strike_from_delta(self, delta: float) -> float:
        phi = self.option_sign
        if delta * phi < 0.0:
            raise ValueError("option type and delta are incoherent")
        if self.delta_type == DeltaType.SPOT:
            if abs(delta) > self.foreign_discount:
                raise ValueError("spot delta out of range")
            arg = -phi * inverse_normal_cdf(phi * delta / self.foreign_discount) * self.stddev + 0.5 * self.stddev * self.stddev
            return self.forward * math.exp(arg)
        if self.delta_type == DeltaType.FWD:
            if abs(delta) > 1.0:
                raise ValueError("forward delta out of range")
            arg = -phi * inverse_normal_cdf(phi * delta) * self.stddev + 0.5 * self.stddev * self.stddev
            return self.forward * math.exp(arg)
        return self._premium_adjusted_strike_from_delta(delta)

    def atm_strike(self, atm_type: AtmType) -> float:
        f_exp_pos = self.forward * math.exp(0.5 * self.stddev * self.stddev)
        f_exp_neg = self.forward * math.exp(-0.5 * self.stddev * self.stddev)
        if atm_type == AtmType.ATM_SPOT:
            return self.spot
        if atm_type == AtmType.ATM_FWD:
            return self.forward
        if atm_type == AtmType.ATM_DELTA_NEUTRAL:
            if self.delta_type in (DeltaType.SPOT, DeltaType.FWD):
                return f_exp_pos
            return f_exp_neg
        if atm_type in (AtmType.ATM_GAMMA_MAX, AtmType.ATM_VEGA_MAX):
            return f_exp_pos
        if atm_type == AtmType.ATM_PUT_CALL_50:
            if self.delta_type != DeltaType.FWD:
                raise ValueError("put/call 50 ATM is only possible for forward delta")
            return f_exp_pos
        raise ValueError(f"invalid ATM type {atm_type}")

    def _premium_adjusted_strike_from_delta(self, delta: float) -> float:
        base_type = DeltaType.SPOT if self.delta_type == DeltaType.PA_SPOT else DeltaType.FWD
        right = BlackDeltaCalculator(
            self.option_sign,
            base_type,
            self.spot,
            self.domestic_discount,
            self.foreign_discount,
            self.stddev,
        ).strike_from_delta(delta)

        def f(strike: float) -> float:
            return self.delta_from_strike(strike) - delta

        if self.option_sign < 0:
            return _bisect(f, 1.0e-12, self.spot * 100.0)

        def g(strike: float) -> float:
            return self._cum_d2(strike) * self.stddev - self._n_d2(strike)

        left = _bisect(g, 1.0e-12, right)
        return _bisect(f, left, right)

    def _cum_d1(self, strike: float) -> float:
        phi = self.option_sign
        if self.stddev >= 1.0e-16 and strike > 0.0:
            d1 = math.log(self.forward / strike) / self.stddev + 0.5 * self.stddev
            return normal_cdf(phi * d1)
        if self.forward < strike:
            return 0.0 if phi > 0 else 1.0
        if self.forward == strike:
            return normal_cdf(phi * 0.5 * self.stddev)
        return 1.0 if phi > 0 else 0.0

    def _cum_d2(self, strike: float) -> float:
        phi = self.option_sign
        if self.stddev >= 1.0e-16 and strike > 0.0:
            d2 = math.log(self.forward / strike) / self.stddev - 0.5 * self.stddev
            return normal_cdf(phi * d2)
        if self.forward < strike:
            return 0.0 if phi > 0 else 1.0
        if self.forward == strike:
            return normal_cdf(-phi * 0.5 * self.stddev)
        return 1.0 if phi > 0 else 0.0

    def _n_d2(self, strike: float) -> float:
        if self.stddev >= 1.0e-16 and strike > 0.0:
            d2 = math.log(self.forward / strike) / self.stddev - 0.5 * self.stddev
            return normal_pdf(d2)
        return 0.0


def _bisect(func, low: float, high: float, accuracy: float = 1.0e-10, max_iterations: int = 200) -> float:
    f_low = func(low)
    f_high = func(high)
    if f_low == 0.0:
        return low
    if f_high == 0.0:
        return high
    if f_low * f_high > 0.0:
        raise ValueError("root is not bracketed")
    for _ in range(max_iterations):
        mid = 0.5 * (low + high)
        f_mid = func(mid)
        if abs(f_mid) < accuracy or abs(high - low) < accuracy:
            return mid
        if f_low * f_mid <= 0.0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return 0.5 * (low + high)
