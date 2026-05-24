from __future__ import annotations

import math
from dataclasses import dataclass

from pyquantlib.math.distributions import normal_cdf, normal_pdf


@dataclass(frozen=True)
class BlackResult:
    value: float
    forward_delta: float
    strike_sensitivity: float
    vega_by_stddev: float
    d1: float
    d2: float


def black_formula(
    option_sign: int,
    forward: float,
    strike: float,
    stddev: float,
    discount: float,
    displacement: float = 0.0,
) -> BlackResult:
    if option_sign not in (-1, 1):
        raise ValueError("option_sign must be 1 for call or -1 for put")
    if displacement < 0.0:
        raise ValueError("displacement must be non-negative")
    if forward + displacement <= 0.0 or strike + displacement < 0.0:
        raise ValueError("forward + displacement must be positive and strike + displacement must be non-negative")
    if discount <= 0.0:
        raise ValueError("discount must be positive")

    if stddev <= 0.0:
        intrinsic = max(option_sign * (forward - strike), 0.0)
        forward_delta = float(option_sign) if intrinsic > 0.0 else 0.0
        strike_sensitivity = -discount * float(option_sign) if intrinsic > 0.0 else 0.0
        return BlackResult(discount * intrinsic, discount * forward_delta, strike_sensitivity, 0.0, math.inf, math.inf)

    displaced_forward = forward + displacement
    displaced_strike = strike + displacement
    if displaced_strike == 0.0:
        value = displaced_forward * discount if option_sign > 0 else 0.0
        return BlackResult(value, discount if option_sign > 0 else 0.0, 0.0, 0.0, math.inf, math.inf)

    d1 = math.log(displaced_forward / displaced_strike) / stddev + 0.5 * stddev
    d2 = d1 - stddev
    nd1 = normal_cdf(option_sign * d1)
    nd2 = normal_cdf(option_sign * d2)
    value = discount * option_sign * (displaced_forward * nd1 - displaced_strike * nd2)
    forward_delta = discount * option_sign * nd1
    strike_sensitivity = -discount * option_sign * nd2
    vega_by_stddev = discount * displaced_forward * normal_pdf(d1)
    return BlackResult(value, forward_delta, strike_sensitivity, vega_by_stddev, d1, d2)
