from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Callable

from pyqlite import (
    Actual360,
    Actual365Fixed,
    AnalyticFxOptionEngine,
    AnalyticDigitalFxOptionEngine,
    BlackCapFloorEngine,
    BlackConstantVol,
    BlackDeltaVolSurface,
    BlackVarianceCurve,
    BlackVarianceSurface,
    BlackSwaptionEngine,
    CapFloor,
    CapFloorType,
    DiscountCurve,
    DiscountingBondEngine,
    DiscountingFraEngine,
    DiscountingFxForwardEngine,
    DiscountingSwapEngine,
    DigitalFxOption,
    FixedRateBond,
    FloatFloatSwap,
    FlatForwardCurve,
    ForwardRateAgreement,
    FxForward,
    FxOption,
    IborIndex,
    NonstandardSwap,
    OptionType,
    OvernightIndexedSwap,
    Period,
    PositionType,
    Schedule,
    SabrParameters,
    SabrSwaptionVolatilityCube,
    SimpleQuote,
    SwapType,
    Swaption,
    SwaptionVolatilityCube,
    SwaptionVolatilityMatrix,
    TimeUnit,
    VanillaSwap,
    WeekendsOnly,
    ZeroCurve,
    DeltaType,
)
from pyqlite.cashflows import ibor_leg

try:
    import xlwings as xw
except ImportError:
    class _XlwingsFallback:
        @staticmethod
        def func(*decorator_args: Any, **decorator_kwargs: Any) -> Callable:
            if decorator_args and callable(decorator_args[0]) and not decorator_kwargs:
                return decorator_args[0]

            def decorator(func: Callable) -> Callable:
                return func

            return decorator

    xw = _XlwingsFallback()


@xw.func
def PYQL_FX_FORWARD_RATE(
    evaluation_date: Any,
    maturity_date: Any,
    spot_fx: float,
    source_rate: float,
    target_rate: float,
    settlement_days: int = 2,
    source_curve: Any = None,
    target_curve: Any = None,
) -> float:
    """Return the fair FX forward rate as target currency per source currency."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    source_curve_obj = _build_curve(eval_date, source_curve, source_rate, "source")
    target_curve_obj = _build_curve(eval_date, target_curve, target_rate, "target")
    spot = _as_float(spot_fx, "spot_fx")
    forward = FxForward.from_forward_rate(
        1.0,
        "SRC",
        "TGT",
        spot,
        maturity,
        pay_source_currency=True,
        settlement_days=_as_int(_default_blank(settlement_days, 2), "settlement_days"),
        settlement_calendar=WeekendsOnly(),
    )
    result = DiscountingFxForwardEngine(source_curve_obj, target_curve_obj, SimpleQuote(spot)).calculate(
        forward,
        eval_date,
    )
    return result.fair_forward_rate


@xw.func
def PYQL_FX_FORWARD_ZERO_NPV_RATE(
    evaluation_date: Any,
    maturity_date: Any,
    spot_fx: float,
    source_rate: float,
    target_rate: float,
    settlement_days: int = 2,
    source_curve: Any = None,
    target_curve: Any = None,
) -> float:
    """Return the contract forward rate that makes NPV zero."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    source_curve_obj = _build_curve(eval_date, source_curve, source_rate, "source")
    target_curve_obj = _build_curve(eval_date, target_curve, target_rate, "target")
    spot = _as_float(spot_fx, "spot_fx")
    forward = FxForward.from_forward_rate(
        1.0,
        "SRC",
        "TGT",
        spot,
        maturity,
        pay_source_currency=True,
        settlement_days=_as_int(_default_blank(settlement_days, 2), "settlement_days"),
        settlement_calendar=WeekendsOnly(),
    )
    result = DiscountingFxForwardEngine(source_curve_obj, target_curve_obj, SimpleQuote(spot)).calculate(
        forward,
        eval_date,
    )
    return result.zero_npv_forward_rate


@xw.func
def PYQL_FX_FORWARD_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    spot_fx: float,
    source_nominal: float,
    contract_forward_rate: float,
    source_rate: float,
    target_rate: float,
    pay_source_currency: bool = True,
    settlement_days: int = 2,
    source_curve: Any = None,
    target_curve: Any = None,
) -> float:
    """Return FX forward NPV in source-currency units."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    source_curve_obj = _build_curve(eval_date, source_curve, source_rate, "source")
    target_curve_obj = _build_curve(eval_date, target_curve, target_rate, "target")
    spot = _as_float(spot_fx, "spot_fx")
    forward = FxForward.from_forward_rate(
        _as_float(source_nominal, "source_nominal"),
        "SRC",
        "TGT",
        _as_float(contract_forward_rate, "contract_forward_rate"),
        maturity,
        pay_source_currency=_as_bool(_default_blank(pay_source_currency, True), "pay_source_currency"),
        settlement_days=_as_int(_default_blank(settlement_days, 2), "settlement_days"),
        settlement_calendar=WeekendsOnly(),
    )
    return DiscountingFxForwardEngine(source_curve_obj, target_curve_obj, SimpleQuote(spot)).calculate(
        forward,
        eval_date,
    ).value


@xw.func
def PYQL_FX_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    spot_fx: float,
    strike: float,
    foreign_notional: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
    vol_surface: Any = None,
) -> float:
    """Return European FX option NPV in domestic-currency units."""
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    option = FxOption(
        _option_type(option_type),
        "DOM",
        "FOR",
        _as_float(foreign_notional, "foreign_notional"),
        _as_float(strike, "strike"),
        expiry,
    )
    domestic_curve_obj = _build_curve(eval_date, domestic_curve, domestic_rate, "domestic")
    foreign_curve_obj = _build_curve(eval_date, foreign_curve, foreign_rate, "foreign")
    spot = _as_float(spot_fx, "spot_fx")
    engine = AnalyticFxOptionEngine(
        SimpleQuote(spot),
        domestic_curve_obj,
        foreign_curve_obj,
        _build_vol(eval_date, vol_surface, volatility, spot, domestic_curve_obj, foreign_curve_obj),
    )
    return engine.calculate(option).value


@xw.func
def PYQL_DIGITAL_FX_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    spot_fx: float,
    strike: float,
    notional: float,
    cash_payoff: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
) -> float:
    """Return cash-or-nothing digital FX option NPV in domestic-currency units."""
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    domestic_curve_obj = _build_curve(eval_date, domestic_curve, domestic_rate, "domestic")
    foreign_curve_obj = _build_curve(eval_date, foreign_curve, foreign_rate, "foreign")
    option = DigitalFxOption(
        _option_type(option_type),
        _as_float(notional, "notional"),
        _as_float(strike, "strike"),
        _as_float(cash_payoff, "cash_payoff"),
        expiry,
    )
    return AnalyticDigitalFxOptionEngine(
        SimpleQuote(_as_float(spot_fx, "spot_fx")),
        domestic_curve_obj,
        foreign_curve_obj,
        BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed()),
    ).calculate(option).value


@xw.func
def PYQL_OIS_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    overnight_rate: float,
    pay_fixed: bool = True,
    frequency_months: int = 12,
    floating_spread: float = 0.0,
    discount_curve: Any = None,
    overnight_curve: Any = None,
) -> float:
    """Return fixed-vs-overnight indexed swap NPV."""
    result = _price_ois(
        evaluation_date,
        maturity_date,
        nominal,
        fixed_rate,
        discount_rate,
        overnight_rate,
        pay_fixed,
        frequency_months,
        floating_spread,
        discount_curve,
        overnight_curve,
    )
    return result.value


@xw.func
def PYQL_OIS_FAIR_RATE(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    discount_rate: float,
    overnight_rate: float,
    pay_fixed: bool = True,
    frequency_months: int = 12,
    floating_spread: float = 0.0,
    discount_curve: Any = None,
    overnight_curve: Any = None,
) -> float:
    """Return the par fixed rate for an overnight indexed swap."""
    result = _price_ois(
        evaluation_date,
        maturity_date,
        nominal,
        0.0,
        discount_rate,
        overnight_rate,
        pay_fixed,
        frequency_months,
        floating_spread,
        discount_curve,
        overnight_curve,
    )
    return result.fair_rate


@xw.func
def PYQL_FLOAT_FLOAT_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    nominal1: float,
    nominal2: float,
    discount_rate: float,
    forward_rate1: float,
    forward_rate2: float,
    spread1: float = 0.0,
    spread2: float = 0.0,
    pay_leg1: bool = True,
    frequency1_months: int = 3,
    frequency2_months: int = 6,
    discount_curve: Any = None,
    forward_curve1: Any = None,
    forward_curve2: Any = None,
) -> float:
    """Return float-float basis swap NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    calendar = WeekendsOnly()
    f1 = _as_int(_default_blank(frequency1_months, 3), "frequency1_months")
    f2 = _as_int(_default_blank(frequency2_months, 6), "frequency2_months")
    schedule1 = Schedule.generate(eval_date, maturity, Period(f1, TimeUnit.MONTHS), calendar=calendar)
    schedule2 = Schedule.generate(eval_date, maturity, Period(f2, TimeUnit.MONTHS), calendar=calendar)
    curve = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    curve1 = _build_curve(eval_date, forward_curve1, forward_rate1, "forward1")
    curve2 = _build_curve(eval_date, forward_curve2, forward_rate2, "forward2")
    index1 = IborIndex("Excel-Ibor-1", Period(f1, TimeUnit.MONTHS), 2, calendar, Actual360(), curve1)
    index2 = IborIndex("Excel-Ibor-2", Period(f2, TimeUnit.MONTHS), 2, calendar, Actual360(), curve2)
    swap = FloatFloatSwap.from_nominals(
        SwapType.PAYER if _as_bool(_default_blank(pay_leg1, True), "pay_leg1") else SwapType.RECEIVER,
        _as_float(nominal1, "nominal1"),
        _as_float(nominal2, "nominal2"),
        schedule1,
        index1,
        Actual360(),
        schedule2,
        index2,
        Actual360(),
        _as_float(_default_blank(spread1, 0.0), "spread1"),
        _as_float(_default_blank(spread2, 0.0), "spread2"),
    )
    return DiscountingSwapEngine(curve).calculate(swap).value


@xw.func
def PYQL_NONSTANDARD_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    fixed_nominals: Any,
    floating_nominals: Any,
    fixed_rates: Any,
    discount_rate: float,
    forward_rate: float,
    pay_fixed: bool = True,
    frequency_months: int = 6,
    gearings: Any = None,
    spreads: Any = None,
    intermediate_capital_exchange: bool = False,
    final_capital_exchange: bool = False,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return nonstandard fixed-vs-floating swap NPV from comma-separated vectors."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    calendar = WeekendsOnly()
    frequency = _as_int(_default_blank(frequency_months, 6), "frequency_months")
    schedule = Schedule.generate(eval_date, maturity, Period(frequency, TimeUnit.MONTHS), calendar=calendar)
    periods = len(schedule.dates) - 1
    fixed_nominals_v = _as_float_vector(fixed_nominals, periods, "fixed_nominals")
    floating_nominals_v = _as_float_vector(floating_nominals, periods, "floating_nominals")
    fixed_rates_v = _as_float_vector(fixed_rates, periods, "fixed_rates")
    gearings_v = _as_float_vector(_default_blank(gearings, 1.0), periods, "gearings")
    spreads_v = _as_float_vector(_default_blank(spreads, 0.0), periods, "spreads")
    curve = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    index = IborIndex("Excel-Ibor", Period(frequency, TimeUnit.MONTHS), 2, calendar, Actual360(), forward_curve_obj)
    swap = NonstandardSwap(
        SwapType.PAYER if _as_bool(_default_blank(pay_fixed, True), "pay_fixed") else SwapType.RECEIVER,
        fixed_nominals_v,
        floating_nominals_v,
        schedule,
        fixed_rates_v,
        Actual360(),
        schedule,
        index,
        gearings_v,
        spreads_v,
        Actual360(),
        _as_bool(_default_blank(intermediate_capital_exchange, False), "intermediate_capital_exchange"),
        _as_bool(_default_blank(final_capital_exchange, False), "final_capital_exchange"),
    )
    return DiscountingSwapEngine(curve).calculate(swap).value


@xw.func
def PYQL_FRA_NPV(
    evaluation_date: Any,
    value_date: Any,
    maturity_date: Any,
    notional: float,
    strike_rate: float,
    forward_rate: float,
    discount_rate: float,
    long_position: bool = True,
    settlement_days: int = 2,
    forward_curve: Any = None,
    discount_curve: Any = None,
) -> float:
    """Return FRA NPV discounted to the evaluation date."""
    eval_date = _as_date(evaluation_date)
    start = _as_future_date(value_date, eval_date, "value_date")
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    calendar = WeekendsOnly()
    index = IborIndex(
        "Excel-Ibor",
        Period(max(1, _months_between(start, maturity)), TimeUnit.MONTHS),
        _as_int(_default_blank(settlement_days, 2), "settlement_days"),
        calendar,
        Actual360(),
        forward_curve_obj,
    )
    fra = ForwardRateAgreement(
        index,
        start,
        maturity,
        PositionType.LONG if _as_bool(_default_blank(long_position, True), "long_position") else PositionType.SHORT,
        _as_float(strike_rate, "strike_rate"),
        _as_float(notional, "notional"),
    )
    return DiscountingFraEngine(discount_curve_obj).calculate(fra, eval_date).value


@xw.func
def PYQL_FIXED_BOND_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    face_amount: float,
    coupon_rate: float,
    discount_rate: float,
    frequency_months: int = 12,
    settlement_days: int = 2,
    discount_curve: Any = None,
) -> float:
    """Return fixed-rate bond NPV on the discount curve."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    frequency = _as_int(_default_blank(frequency_months, 12), "frequency_months")
    if frequency <= 0:
        raise ValueError(f"frequency_months must be positive, got {frequency}")
    calendar = WeekendsOnly()
    schedule = Schedule.generate(
        eval_date,
        maturity,
        Period(frequency, TimeUnit.MONTHS),
        calendar=calendar,
    )
    bond = FixedRateBond.from_schedule(
        _as_int(_default_blank(settlement_days, 2), "settlement_days"),
        _as_float(face_amount, "face_amount"),
        schedule,
        _as_float(coupon_rate, "coupon_rate"),
        Actual365Fixed(),
        payment_calendar=calendar,
    )
    curve = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    return DiscountingBondEngine(curve).calculate(bond, eval_date).value


@xw.func
def PYQL_CAPFLOOR_NPV(
    cap_floor_type: str,
    evaluation_date: Any,
    start_date: Any,
    maturity_date: Any,
    notional: float,
    cap_rate: Any,
    floor_rate: Any,
    forward_rate: float,
    discount_rate: float,
    volatility: float,
    frequency_months: int = 6,
    floating_spread: float = 0.0,
    forward_curve: Any = None,
    discount_curve: Any = None,
) -> float:
    """Return cap, floor, or collar NPV using the Black cap/floor engine."""
    eval_date = _as_date(evaluation_date)
    start = _as_future_date(start_date, eval_date, "start_date")
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    frequency = _as_int(_default_blank(frequency_months, 6), "frequency_months")
    if frequency <= 0:
        raise ValueError(f"frequency_months must be positive, got {frequency}")
    calendar = WeekendsOnly()
    schedule = Schedule.generate(start, maturity, Period(frequency, TimeUnit.MONTHS), calendar=calendar)
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    index = IborIndex("Excel-Ibor", Period(frequency, TimeUnit.MONTHS), 2, calendar, Actual360(), forward_curve_obj)
    leg = ibor_leg(
        schedule,
        _as_float(notional, "notional"),
        index,
        _as_float(_default_blank(floating_spread, 0.0), "floating_spread"),
        Actual360(),
    )
    normalized = str(cap_floor_type).strip().upper()
    if normalized == "CAP":
        instrument = CapFloor.cap(leg, (_as_float(cap_rate, "cap_rate"),))
    elif normalized == "FLOOR":
        instrument = CapFloor.floor(leg, (_as_float(floor_rate, "floor_rate"),))
    elif normalized == "COLLAR":
        instrument = CapFloor.collar(
            leg,
            (_as_float(cap_rate, "cap_rate"),),
            (_as_float(floor_rate, "floor_rate"),),
        )
    else:
        raise ValueError("cap_floor_type must be CAP, FLOOR, or COLLAR")
    vol = BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed())
    return BlackCapFloorEngine(discount_curve_obj, vol).calculate(instrument).value


@xw.func
def PYQL_SWAPTION_NPV(
    evaluation_date: Any,
    exercise_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    forward_rate: float,
    volatility: float,
    pay_fixed: bool = True,
    fixed_frequency_months: int = 6,
    floating_frequency_months: int = 6,
    floating_spread: float = 0.0,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return physical European swaption NPV using the Black swaption engine."""
    eval_date = _as_date(evaluation_date)
    exercise = _as_future_date(exercise_date, eval_date, "exercise_date")
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    fixed_frequency = _as_int(_default_blank(fixed_frequency_months, 6), "fixed_frequency_months")
    floating_frequency = _as_int(_default_blank(floating_frequency_months, 6), "floating_frequency_months")
    calendar = WeekendsOnly()
    fixed_schedule = Schedule.generate(exercise, maturity, Period(fixed_frequency, TimeUnit.MONTHS), calendar=calendar)
    floating_schedule = Schedule.generate(exercise, maturity, Period(floating_frequency, TimeUnit.MONTHS), calendar=calendar)
    index = IborIndex("Excel-Ibor", Period(floating_frequency, TimeUnit.MONTHS), 2, calendar, Actual360(), forward_curve_obj)
    swap = VanillaSwap(
        SwapType.PAYER if _as_bool(_default_blank(pay_fixed, True), "pay_fixed") else SwapType.RECEIVER,
        _as_float(nominal, "nominal"),
        fixed_schedule,
        _as_float(fixed_rate, "fixed_rate"),
        Actual360(),
        floating_schedule,
        index,
        _as_float(_default_blank(floating_spread, 0.0), "floating_spread"),
        Actual360(),
    )
    vol = _build_swaption_vol(eval_date, volatility)
    return BlackSwaptionEngine(discount_curve_obj, vol).calculate(Swaption(swap, exercise)).value


@xw.func
def PYQL_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    forward_rate: float,
    pay_fixed: bool = True,
    fixed_frequency_months: int = 6,
    floating_frequency_months: int = 6,
    floating_spread: float = 0.0,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return fixed-vs-floating swap NPV."""
    result = _price_swap(
        evaluation_date,
        maturity_date,
        nominal,
        fixed_rate,
        discount_rate,
        forward_rate,
        pay_fixed,
        fixed_frequency_months,
        floating_frequency_months,
        floating_spread,
        discount_curve,
        forward_curve,
    )
    return result.value


@xw.func
def PYQL_SWAP_FAIR_RATE(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    discount_rate: float,
    forward_rate: float,
    pay_fixed: bool = True,
    fixed_frequency_months: int = 6,
    floating_frequency_months: int = 6,
    floating_spread: float = 0.0,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return the par fixed rate for a fixed-vs-floating swap."""
    result = _price_swap(
        evaluation_date,
        maturity_date,
        nominal,
        0.0,
        discount_rate,
        forward_rate,
        pay_fixed,
        fixed_frequency_months,
        floating_frequency_months,
        floating_spread,
        discount_curve,
        forward_curve,
    )
    return result.fair_rate


def _price_swap(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    forward_rate: float,
    pay_fixed: bool,
    fixed_frequency_months: int,
    floating_frequency_months: int,
    floating_spread: float,
    discount_curve: Any = None,
    forward_curve: Any = None,
):
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    calendar = WeekendsOnly()
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    fixed_frequency = _as_int(_default_blank(fixed_frequency_months, 6), "fixed_frequency_months")
    floating_frequency = _as_int(_default_blank(floating_frequency_months, 6), "floating_frequency_months")
    if maturity <= eval_date:
        raise ValueError(f"maturity_date {maturity} must be after evaluation_date {eval_date}")
    if fixed_frequency <= 0:
        raise ValueError(f"fixed_frequency_months must be positive, got {fixed_frequency}")
    if floating_frequency <= 0:
        raise ValueError(f"floating_frequency_months must be positive, got {floating_frequency}")
    fixed_schedule = Schedule.generate(
        eval_date,
        maturity,
        Period(fixed_frequency, TimeUnit.MONTHS),
        calendar=calendar,
    )
    floating_schedule = Schedule.generate(
        eval_date,
        maturity,
        Period(floating_frequency, TimeUnit.MONTHS),
        calendar=calendar,
    )
    index = IborIndex(
        "Excel-Ibor",
        Period(floating_frequency, TimeUnit.MONTHS),
        2,
        calendar,
        Actual360(),
        forward_curve_obj,
    )
    swap = VanillaSwap(
        SwapType.PAYER if _as_bool(_default_blank(pay_fixed, True), "pay_fixed") else SwapType.RECEIVER,
        _as_float(nominal, "nominal"),
        fixed_schedule,
        _as_float(fixed_rate, "fixed_rate"),
        Actual360(),
        floating_schedule,
        index,
        _as_float(_default_blank(floating_spread, 0.0), "floating_spread"),
        Actual360(),
    )
    return DiscountingSwapEngine(discount_curve_obj).calculate(swap)


def _price_ois(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    overnight_rate: float,
    pay_fixed: bool,
    frequency_months: int,
    floating_spread: float,
    discount_curve: Any = None,
    overnight_curve: Any = None,
):
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    calendar = WeekendsOnly()
    frequency = _as_int(_default_blank(frequency_months, 12), "frequency_months")
    if maturity <= eval_date:
        raise ValueError(f"maturity_date {maturity} must be after evaluation_date {eval_date}")
    if frequency <= 0:
        raise ValueError(f"frequency_months must be positive, got {frequency}")
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    overnight_curve_obj = _build_curve(eval_date, overnight_curve, overnight_rate, "overnight")
    schedule = Schedule.generate(eval_date, maturity, Period(frequency, TimeUnit.MONTHS), calendar=calendar)
    overnight_index = IborIndex(
        "Excel-ON",
        Period(1, TimeUnit.DAYS),
        0,
        calendar,
        Actual360(),
        overnight_curve_obj,
    )
    swap = OvernightIndexedSwap.from_nominal(
        SwapType.PAYER if _as_bool(_default_blank(pay_fixed, True), "pay_fixed") else SwapType.RECEIVER,
        _as_float(nominal, "nominal"),
        schedule,
        _as_float(fixed_rate, "fixed_rate"),
        Actual360(),
        overnight_index,
        _as_float(_default_blank(floating_spread, 0.0), "floating_spread"),
    )
    return DiscountingSwapEngine(discount_curve_obj).calculate(swap)


def _build_curve(reference_date: date, curve_spec: Any, fallback_rate: Any, name: str):
    if curve_spec not in (None, ""):
        curve_type, nodes = _parse_curve_spec(curve_spec, reference_date)
        dates = tuple(node_date for node_date, _ in nodes)
        values = tuple(value for _, value in nodes)
        if curve_type == "zero":
            return ZeroCurve(reference_date, dates, values, Actual365Fixed())
        if curve_type == "discount":
            return DiscountCurve(reference_date, dates, values, Actual365Fixed())
        raise ValueError(f"unsupported {name}_curve type {curve_type!r}")
    return FlatForwardCurve(reference_date, _as_float(fallback_rate, f"{name}_rate"), Actual365Fixed())


def _parse_curve_spec(value: Any, reference_date: date) -> tuple[str, list[tuple[date, float]]]:
    text = str(value).strip()
    if not text:
        raise ValueError("curve specification is blank")
    curve_type = "zero"
    if text.lower().startswith("discount|"):
        curve_type = "discount"
        text = text.split("|", 1)[1]
    elif text.lower().startswith("zero|"):
        text = text.split("|", 1)[1]
    nodes = []
    for item in text.replace("\n", ";").split(";"):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"curve node must be date:value, got {item!r}")
        raw_date, raw_value = item.split(":", 1)
        pillar = _as_future_date(raw_date.strip(), reference_date, "curve pillar")
        nodes.append((pillar, _as_float(raw_value.strip(), "curve node value")))
    if not nodes:
        raise ValueError("curve specification contains no nodes")
    nodes.sort(key=lambda item: item[0])
    return curve_type, nodes


def _build_vol(reference_date: date, vol_spec: Any, fallback_vol: Any, spot: float, domestic_curve, foreign_curve):
    if vol_spec in (None, ""):
        return BlackConstantVol(reference_date, _as_float(fallback_vol, "volatility"), Actual365Fixed())
    text = str(vol_spec).strip()
    if not text:
        return BlackConstantVol(reference_date, _as_float(fallback_vol, "volatility"), Actual365Fixed())
    if text.lower().startswith("strike|"):
        text = text.split("|", 1)[1]
        strikes, dates, vols = _parse_surface_spec(text, reference_date)
        return BlackVarianceSurface(reference_date, dates, strikes, vols, Actual365Fixed())
    if "|" in text:
        put_deltas, has_atm, call_deltas, dates, vols = _parse_delta_surface_spec(text, reference_date)
        return BlackDeltaVolSurface(
            reference_date,
            dates,
            put_deltas,
            call_deltas,
            has_atm,
            vols,
            spot,
            domestic_curve,
            foreign_curve,
            Actual365Fixed(),
            DeltaType.SPOT,
        )
    dates, vols = _parse_vol_curve_spec(text, reference_date)
    return BlackVarianceCurve(reference_date, dates, vols, Actual365Fixed())


def _build_swaption_vol(reference_date: date, vol_spec: Any):
    if vol_spec in (None, ""):
        raise ValueError("volatility is required")
    if isinstance(vol_spec, (int, float)):
        return BlackConstantVol(reference_date, float(vol_spec), Actual365Fixed())
    text = str(vol_spec).strip()
    if not text:
        raise ValueError("volatility is required")
    if "|" not in text:
        return BlackConstantVol(reference_date, _as_float(text, "volatility"), Actual365Fixed())
    kind, *parts = [part.strip() for part in text.split("|")]
    normalized = kind.lower()
    if normalized == "matrix":
        if len(parts) != 3:
            raise ValueError("swaption vol matrix must be matrix|optionTenors|swapTenors|rows")
        return SwaptionVolatilityMatrix(
            reference_date,
            _parse_tenors(parts[0], "optionTenors"),
            _parse_tenors(parts[1], "swapTenors"),
            _parse_float_rows(parts[2], "volatility rows"),
            Actual365Fixed(),
        )
    if normalized == "cube":
        if len(parts) != 5:
            raise ValueError("swaption vol cube must be cube|optionTenors|swapTenors|atmRows|strikeSpreads|layers")
        atm = SwaptionVolatilityMatrix(
            reference_date,
            _parse_tenors(parts[0], "optionTenors"),
            _parse_tenors(parts[1], "swapTenors"),
            _parse_float_rows(parts[2], "ATM volatility rows"),
            Actual365Fixed(),
        )
        strike_spreads = tuple(_as_float(item.strip(), "strike spread") for item in parts[3].split(",") if item.strip())
        layers = tuple(_parse_float_rows(layer, "vol-spread layer") for layer in parts[4].split("#") if layer.strip())
        return SwaptionVolatilityCube(atm, strike_spreads, layers)
    if normalized == "sabr":
        if len(parts) != 4:
            raise ValueError("swaption SABR vol must be sabr|optionTenors|swapTenors|atmRows|parameterRows")
        atm = SwaptionVolatilityMatrix(
            reference_date,
            _parse_tenors(parts[0], "optionTenors"),
            _parse_tenors(parts[1], "swapTenors"),
            _parse_float_rows(parts[2], "ATM volatility rows"),
            Actual365Fixed(),
        )
        return SabrSwaptionVolatilityCube(atm, _parse_sabr_rows(parts[3]))
    raise ValueError("swaption volatility must be a number, matrix|..., cube|..., or sabr|...")


def _parse_tenors(value: str, name: str) -> tuple[Period, ...]:
    tenors = tuple(_parse_tenor(token.strip(), name) for token in value.split(",") if token.strip())
    if not tenors:
        raise ValueError(f"{name} must contain at least one tenor")
    return tenors


def _parse_tenor(value: str, name: str) -> Period:
    if len(value) < 2:
        raise ValueError(f"{name} tenor must look like 1Y, 6M, 2W, or 10D")
    unit = value[-1].upper()
    length = _as_int(value[:-1], name)
    if unit == "Y":
        return Period(length, TimeUnit.YEARS)
    if unit == "M":
        return Period(length, TimeUnit.MONTHS)
    if unit == "W":
        return Period(length, TimeUnit.WEEKS)
    if unit == "D":
        return Period(length, TimeUnit.DAYS)
    raise ValueError(f"{name} tenor unit must be Y, M, W, or D")


def _parse_float_rows(value: str, name: str) -> tuple[tuple[float, ...], ...]:
    rows = []
    for row_text in value.replace("\n", ";").split(";"):
        row_text = row_text.strip()
        if not row_text:
            continue
        rows.append(tuple(_as_float(item.strip(), name) for item in row_text.split(",") if item.strip()))
    if not rows:
        raise ValueError(f"{name} contains no rows")
    return tuple(rows)


def _parse_sabr_rows(value: str) -> tuple[tuple[SabrParameters, ...], ...]:
    rows = []
    for row_text in value.replace("\n", ";").split(";"):
        row_text = row_text.strip()
        if not row_text:
            continue
        row = []
        for cell in row_text.split("/"):
            params = tuple(_as_float(item.strip(), "SABR parameter") for item in cell.split(",") if item.strip())
            if len(params) != 4:
                raise ValueError("each SABR parameter cell must contain alpha,beta,nu,rho")
            row.append(SabrParameters(params[0], params[1], params[2], params[3]))
        rows.append(tuple(row))
    if not rows:
        raise ValueError("SABR parameter rows contain no data")
    return tuple(rows)


def _parse_vol_curve_spec(value: str, reference_date: date) -> tuple[tuple[date, ...], tuple[float, ...]]:
    nodes = []
    for item in value.replace("\n", ";").split(";"):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"vol curve node must be date:vol, got {item!r}")
        raw_date, raw_vol = item.split(":", 1)
        nodes.append((_as_future_date(raw_date.strip(), reference_date, "vol pillar"), _as_float(raw_vol.strip(), "vol node")))
    if not nodes:
        raise ValueError("vol curve contains no nodes")
    nodes.sort(key=lambda item: item[0])
    return tuple(node[0] for node in nodes), tuple(node[1] for node in nodes)


def _parse_surface_spec(value: str, reference_date: date) -> tuple[tuple[float, ...], tuple[date, ...], tuple[tuple[float, ...], ...]]:
    pieces = [piece.strip() for piece in value.replace("\n", ";").split("|") if piece.strip()]
    if len(pieces) < 2:
        raise ValueError("vol surface must be strikes|date:vols|date:vols")
    strikes = tuple(_as_float(item.strip(), "surface strike") for item in pieces[0].split(",") if item.strip())
    rows = []
    for piece in pieces[1:]:
        if ":" not in piece:
            raise ValueError(f"vol surface row must be date:vol,vol,... got {piece!r}")
        raw_date, raw_vols = piece.split(":", 1)
        row = tuple(_as_float(item.strip(), "surface vol") for item in raw_vols.split(",") if item.strip())
        rows.append((_as_future_date(raw_date.strip(), reference_date, "surface expiry"), row))
    rows.sort(key=lambda item: item[0])
    return strikes, tuple(row[0] for row in rows), tuple(row[1] for row in rows)


def _parse_delta_surface_spec(value: str, reference_date: date):
    pieces = [piece.strip() for piece in value.replace("\n", ";").split("|") if piece.strip()]
    if len(pieces) < 2:
        raise ValueError("delta vol surface must be deltas|date:vols|date:vols")
    put_deltas = []
    call_deltas = []
    has_atm = False
    for token in pieces[0].split(","):
        token = token.strip().upper()
        if not token:
            continue
        if token == "ATM":
            if has_atm:
                raise ValueError("delta vol surface can only contain one ATM column")
            has_atm = True
            continue
        delta = _as_float(token, "surface delta")
        if delta < 0.0:
            put_deltas.append(delta)
        elif delta > 0.0:
            call_deltas.append(delta)
        else:
            raise ValueError("delta surface cannot contain zero delta")
    rows = []
    expected_columns = len(put_deltas) + (1 if has_atm else 0) + len(call_deltas)
    for piece in pieces[1:]:
        if ":" not in piece:
            raise ValueError(f"vol surface row must be date:vol,vol,... got {piece!r}")
        raw_date, raw_vols = piece.split(":", 1)
        row = tuple(_as_float(item.strip(), "surface vol") for item in raw_vols.split(",") if item.strip())
        if len(row) != expected_columns:
            raise ValueError(f"delta vol row has {len(row)} vols but expected {expected_columns}")
        rows.append((_as_future_date(raw_date.strip(), reference_date, "surface expiry"), row))
    rows.sort(key=lambda item: item[0])
    return tuple(put_deltas), has_atm, tuple(call_deltas), tuple(row[0] for row in rows), tuple(row[1] for row in rows)


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError("expected an Excel date value, got a blank cell")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"expected date as yyyy-mm-dd text, got {value!r}") from exc
    if isinstance(value, (int, float)):
        # Excel's 1900 date system serial number. This is what xlwings normally
        # exposes when a cell is formatted as a general number instead of a date.
        return date(1899, 12, 30) + timedelta(days=int(value))
    raise TypeError(f"expected an Excel date value, got {type(value).__name__}")


def _as_future_date(value: Any, anchor: date, name: str) -> date:
    result = _as_date(value)
    if result > anchor:
        return result

    repaired = result
    while repaired <= anchor and repaired.year + 100 <= anchor.year + 100:
        repaired = _add_years(repaired, 100)
    if repaired > anchor:
        return repaired
    raise ValueError(f"{name} {result} must be after evaluation_date {anchor}")


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + years)


def _months_between(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + end.month - start.month
    return max(1, months)


def _default_blank(value: Any, default: Any) -> Any:
    return default if value is None or value == "" else value


def _as_float(value: Any, name: str) -> float:
    if value is None or value == "":
        raise ValueError(f"{name} is required")
    return float(value)


def _as_float_vector(value: Any, length: int, name: str) -> tuple[float, ...]:
    if value is None or value == "":
        raise ValueError(f"{name} is required")
    if isinstance(value, (int, float)):
        return (float(value),) * length
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace("\n", ";").replace(",", ";").split(";") if piece.strip()]
        values = tuple(float(piece) for piece in pieces)
    elif isinstance(value, (list, tuple)):
        flattened = []
        for item in value:
            if isinstance(item, (list, tuple)):
                flattened.extend(item)
            else:
                flattened.append(item)
        values = tuple(float(item) for item in flattened if item not in (None, ""))
    else:
        values = (float(value),)
    if len(values) == 1 and length != 1:
        return values * length
    if len(values) != length:
        raise ValueError(f"{name} has {len(values)} values but expected {length}")
    return values


def _as_int(value: Any, name: str) -> int:
    if value is None or value == "":
        raise ValueError(f"{name} is required")
    return int(float(value))


def _as_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        raise ValueError(f"{name} is required")
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in ("TRUE", "T", "YES", "Y", "1"):
            return True
        if normalized in ("FALSE", "F", "NO", "N", "0"):
            return False
    raise ValueError(f"{name} must be TRUE or FALSE")


def _option_type(value: str) -> OptionType:
    normalized = value.strip().upper()
    if normalized in ("C", "CALL"):
        return OptionType.CALL
    if normalized in ("P", "PUT"):
        return OptionType.PUT
    raise ValueError("option_type must be CALL, C, PUT, or P")
