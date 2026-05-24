from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Callable

from pyquantlib import (
    Actual360,
    Actual365Fixed,
    AnalyticFxOptionEngine,
    AnalyticDigitalFxOptionEngine,
    AnalyticCommodityOptionEngine,
    AnalyticEquityOptionEngine,
    BlackCdsOptionEngine,
    BlackCapFloorEngine,
    BlackConstantVol,
    BlackDeltaVolSurface,
    BlackVarianceCurve,
    BlackVarianceSurface,
    BlackSwaptionEngine,
    BermudanSwaption,
    CapFloor,
    CapFloorType,
    CdsOption,
    CmsSwap,
    CommodityForward,
    CommodityOption,
    CommoditySwap,
    CreditDefaultSwap,
    CrossCurrencyBasisSwap,
    CrossCurrencyFixedFloatSwap,
    DiscountCurve,
    DiscountingBondEngine,
    DiscountingCmsSwapEngine,
    DiscountingCommodityForwardEngine,
    DiscountingCommoditySwapEngine,
    DiscountingCrossCurrencySwapEngine,
    DiscountingEquityTotalReturnSwapEngine,
    DiscountingFraEngine,
    DiscountingFxForwardEngine,
    DiscountingInflationSwapEngine,
    DiscountingSwapEngine,
    DigitalFxOption,
    EquityAsianOption,
    EquityBarrierDirection,
    EquityBarrierOption,
    EquityBarrierStyle,
    EquityOption,
    EquityTotalReturnSwap,
    FixedRateBond,
    FloatFloatSwap,
    FlatHazardRate,
    FlatForwardCurve,
    ForwardRateAgreement,
    FxForward,
    FxOption,
    IborIndex,
    LsmBermudanSwaptionEngine,
    McEquityExoticEngine,
    MidPointCdsEngine,
    NonstandardSwap,
    OptionType,
    OvernightIndexedSwap,
    Period,
    PositionType,
    ProtectionSide,
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
    VarianceSwap,
    VarianceSwapEngine,
    VolatilitySwap,
    VolatilitySwapEngine,
    WeekendsOnly,
    YearOnYearInflationSwap,
    ZeroCurve,
    ZeroCouponInflationSwap,
    ZeroInflationCurve,
    DeltaType,
)
from pyquantlib.cashflows import ibor_leg

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
def PYQUANTLIB_FX_FORWARD_RATE(
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
def PYQUANTLIB_FX_FORWARD_ZERO_NPV_RATE(
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
def PYQUANTLIB_FX_FORWARD_NPV(
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
def PYQUANTLIB_FX_OPTION_NPV(
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
def PYQUANTLIB_DIGITAL_FX_OPTION_NPV(
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
def PYQUANTLIB_OIS_NPV(
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
def PYQUANTLIB_OIS_FAIR_RATE(
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
def PYQUANTLIB_FLOAT_FLOAT_NPV(
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
def PYQUANTLIB_NONSTANDARD_SWAP_NPV(
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
def PYQUANTLIB_BERMUDAN_SWAPTION_NPV(
    evaluation_date: Any,
    exercise_dates: Any,
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
    paths: int = 1024,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return physical Bermudan swaption NPV using the standalone LSM engine."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    exercises = _as_date_vector(exercise_dates, eval_date, "exercise_dates")
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    calendar = WeekendsOnly()
    fixed_frequency = _as_int(_default_blank(fixed_frequency_months, 6), "fixed_frequency_months")
    floating_frequency = _as_int(_default_blank(floating_frequency_months, 6), "floating_frequency_months")
    fixed_schedule = Schedule.generate(exercises[0], maturity, Period(fixed_frequency, TimeUnit.MONTHS), calendar=calendar)
    floating_schedule = Schedule.generate(exercises[0], maturity, Period(floating_frequency, TimeUnit.MONTHS), calendar=calendar)
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
    vol = BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed())
    return LsmBermudanSwaptionEngine(discount_curve_obj, vol, paths=_as_int(_default_blank(paths, 1024), "paths")).calculate(
        BermudanSwaption(swap, exercises)
    ).value


@xw.func
def PYQUANTLIB_CMS_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    forward_rate: float,
    cms_tenor_months: int = 60,
    pay_fixed: bool = True,
    frequency_months: int = 12,
    spread: float = 0.0,
    gearing: float = 1.0,
    volatility: Any = None,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return fixed-vs-CMS swap NPV with optional swaption-vol convexity adjustment."""
    return _price_cms_swap(
        evaluation_date,
        maturity_date,
        nominal,
        fixed_rate,
        discount_rate,
        forward_rate,
        cms_tenor_months,
        pay_fixed,
        frequency_months,
        spread,
        gearing,
        volatility,
        discount_curve,
        forward_curve,
    ).value


@xw.func
def PYQUANTLIB_CMS_SWAP_FAIR_RATE(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    discount_rate: float,
    forward_rate: float,
    cms_tenor_months: int = 60,
    pay_fixed: bool = True,
    frequency_months: int = 12,
    spread: float = 0.0,
    gearing: float = 1.0,
    volatility: Any = None,
    discount_curve: Any = None,
    forward_curve: Any = None,
) -> float:
    """Return the par fixed rate for a fixed-vs-CMS swap."""
    return _price_cms_swap(
        evaluation_date,
        maturity_date,
        nominal,
        0.0,
        discount_rate,
        forward_rate,
        cms_tenor_months,
        pay_fixed,
        frequency_months,
        spread,
        gearing,
        volatility,
        discount_curve,
        forward_curve,
    ).fair_rate


@xw.func
def PYQUANTLIB_XCCY_BASIS_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    pay_nominal: float,
    receive_nominal: float,
    spot_fx: float,
    domestic_rate: float,
    foreign_rate: float,
    pay_spread: float = 0.0,
    receive_spread: float = 0.0,
    pay_leg_domestic: bool = True,
    frequency_months: int = 6,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
) -> float:
    """Return constant-notional cross-currency basis swap NPV in domestic currency."""
    result = _price_xccy_basis(
        evaluation_date,
        maturity_date,
        pay_nominal,
        receive_nominal,
        spot_fx,
        domestic_rate,
        foreign_rate,
        pay_spread,
        receive_spread,
        pay_leg_domestic,
        frequency_months,
        domestic_curve,
        foreign_curve,
    )
    return result.value


@xw.func
def PYQUANTLIB_XCCY_BASIS_SWAP_FAIR_PAY_SPREAD(
    evaluation_date: Any,
    maturity_date: Any,
    pay_nominal: float,
    receive_nominal: float,
    spot_fx: float,
    domestic_rate: float,
    foreign_rate: float,
    pay_spread: float = 0.0,
    receive_spread: float = 0.0,
    pay_leg_domestic: bool = True,
    frequency_months: int = 6,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
) -> float:
    """Return the fair spread on the pay leg of a cross-currency basis swap."""
    result = _price_xccy_basis(
        evaluation_date,
        maturity_date,
        pay_nominal,
        receive_nominal,
        spot_fx,
        domestic_rate,
        foreign_rate,
        pay_spread,
        receive_spread,
        pay_leg_domestic,
        frequency_months,
        domestic_curve,
        foreign_curve,
    )
    return result.fair_pay_spread


@xw.func
def PYQUANTLIB_XCCY_FIXED_FLOAT_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    fixed_nominal: float,
    float_nominal: float,
    spot_fx: float,
    fixed_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    float_spread: float = 0.0,
    pay_fixed: bool = True,
    fixed_leg_domestic: bool = True,
    frequency_months: int = 6,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
) -> float:
    """Return constant-notional cross-currency fixed-float swap NPV in domestic currency."""
    return _price_xccy_fixed_float(
        evaluation_date,
        maturity_date,
        fixed_nominal,
        float_nominal,
        spot_fx,
        fixed_rate,
        domestic_rate,
        foreign_rate,
        float_spread,
        pay_fixed,
        fixed_leg_domestic,
        frequency_months,
        domestic_curve,
        foreign_curve,
    ).value


@xw.func
def PYQUANTLIB_EQUITY_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    spot: float,
    strike: float,
    quantity: float,
    risk_free_rate: float,
    dividend_rate: float,
    volatility: float,
) -> float:
    """Return European equity option NPV under Black-Scholes-Merton."""
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    engine = AnalyticEquityOptionEngine(
        SimpleQuote(_as_float(spot, "spot")),
        FlatForwardCurve(eval_date, _as_float(dividend_rate, "dividend_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(risk_free_rate, "risk_free_rate"), Actual365Fixed()),
        BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed()),
    )
    return engine.calculate(EquityOption(_option_type(option_type), _as_float(quantity, "quantity"), _as_float(strike, "strike"), expiry)).value


@xw.func
def PYQUANTLIB_EQUITY_BARRIER_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    spot: float,
    strike: float,
    quantity: float,
    barrier: float,
    direction: str,
    style: str,
    risk_free_rate: float,
    dividend_rate: float,
    volatility: float,
    paths: int = 1024,
) -> float:
    """Return equity single-barrier option NPV under the MC exotic engine."""
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    engine = _equity_exotic_engine(eval_date, spot, risk_free_rate, dividend_rate, volatility, paths)
    option = EquityBarrierOption(
        _option_type(option_type),
        _as_float(quantity, "quantity"),
        _as_float(strike, "strike"),
        _as_float(barrier, "barrier"),
        _equity_barrier_direction(direction),
        _equity_barrier_style(style),
        expiry,
    )
    return engine.calculate_barrier(option).value


@xw.func
def PYQUANTLIB_EQUITY_ASIAN_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    spot: float,
    strike: float,
    quantity: float,
    risk_free_rate: float,
    dividend_rate: float,
    volatility: float,
    paths: int = 1024,
) -> float:
    """Return equity average-rate Asian option NPV under the MC exotic engine."""
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    engine = _equity_exotic_engine(eval_date, spot, risk_free_rate, dividend_rate, volatility, paths)
    return engine.calculate_asian(EquityAsianOption(_option_type(option_type), _as_float(quantity, "quantity"), _as_float(strike, "strike"), expiry)).value


@xw.func
def PYQUANTLIB_EQUITY_TRS_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    notional: float,
    spot: float,
    initial_price: float,
    risk_free_rate: float,
    dividend_rate: float,
    funding_rate: float,
    funding_spread: float = 0.0,
    receive_equity: bool = True,
    frequency_months: int = 3,
) -> float:
    """Return equity total-return swap NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    calendar = WeekendsOnly()
    schedule = Schedule.generate(eval_date, maturity, Period(_as_int(_default_blank(frequency_months, 3), "frequency_months"), TimeUnit.MONTHS), calendar=calendar)
    discount = FlatForwardCurve(eval_date, _as_float(risk_free_rate, "risk_free_rate"), Actual365Fixed())
    swap = EquityTotalReturnSwap(
        SwapType.RECEIVER if _as_bool(_default_blank(receive_equity, True), "receive_equity") else SwapType.PAYER,
        _as_float(notional, "notional"),
        _as_float(initial_price, "initial_price"),
        maturity,
        schedule,
        _as_float(_default_blank(funding_spread, 0.0), "funding_spread"),
        Actual360(),
    )
    return DiscountingEquityTotalReturnSwapEngine(
        SimpleQuote(_as_float(spot, "spot")),
        FlatForwardCurve(eval_date, _as_float(dividend_rate, "dividend_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(funding_rate, "funding_rate"), Actual365Fixed()),
        discount,
    ).calculate(swap).value


@xw.func
def PYQUANTLIB_COMMODITY_FORWARD_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    spot: float,
    quantity: float,
    contract_price: float,
    forward_rate: float,
    discount_rate: float,
    long_position: bool = True,
) -> float:
    """Return commodity forward NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    engine = DiscountingCommodityForwardEngine(
        FlatForwardCurve(eval_date, _as_float(forward_rate, "forward_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed()),
        SimpleQuote(_as_float(spot, "spot")),
    )
    return engine.calculate(CommodityForward(_position_type(long_position), _as_float(quantity, "quantity"), _as_float(contract_price, "contract_price"), maturity)).value


@xw.func
def PYQUANTLIB_COMMODITY_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    spot: float,
    quantity: float,
    fixed_price: float,
    forward_rate: float,
    discount_rate: float,
    receive_floating: bool = True,
    frequency_months: int = 1,
) -> float:
    """Return commodity fixed-vs-floating swap NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    schedule = Schedule.generate(eval_date, maturity, Period(_as_int(_default_blank(frequency_months, 1), "frequency_months"), TimeUnit.MONTHS), calendar=WeekendsOnly())
    engine = DiscountingCommoditySwapEngine(
        FlatForwardCurve(eval_date, _as_float(forward_rate, "forward_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed()),
        SimpleQuote(_as_float(spot, "spot")),
    )
    return engine.calculate(
        CommoditySwap(SwapType.RECEIVER if _as_bool(_default_blank(receive_floating, True), "receive_floating") else SwapType.PAYER, _as_float(quantity, "quantity"), _as_float(fixed_price, "fixed_price"), schedule)
    ).value


@xw.func
def PYQUANTLIB_COMMODITY_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    spot: float,
    quantity: float,
    strike: float,
    forward_rate: float,
    discount_rate: float,
    volatility: float,
) -> float:
    """Return commodity option NPV using Black on forwards."""
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    engine = AnalyticCommodityOptionEngine(
        FlatForwardCurve(eval_date, _as_float(forward_rate, "forward_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed()),
        BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed()),
        SimpleQuote(_as_float(spot, "spot")),
    )
    return engine.calculate(CommodityOption(_option_type(option_type), _as_float(quantity, "quantity"), _as_float(strike, "strike"), expiry)).value


@xw.func
def PYQUANTLIB_CDS_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    notional: float,
    running_spread: float,
    hazard_rate: float,
    recovery_rate: float,
    discount_rate: float,
    buy_protection: bool = True,
    frequency_months: int = 3,
) -> float:
    """Return CDS NPV using the midpoint default engine."""
    cds, default_curve, discount_curve = _build_cds(evaluation_date, maturity_date, notional, running_spread, hazard_rate, discount_rate, buy_protection, frequency_months)
    return MidPointCdsEngine(default_curve, _as_float(recovery_rate, "recovery_rate"), discount_curve).calculate(cds).value


@xw.func
def PYQUANTLIB_CDS_OPTION_NPV(
    option_type: str,
    evaluation_date: Any,
    expiry_date: Any,
    maturity_date: Any,
    notional: float,
    running_spread: float,
    strike_spread: float,
    hazard_rate: float,
    recovery_rate: float,
    discount_rate: float,
    volatility: float,
    buy_protection: bool = True,
    frequency_months: int = 3,
) -> float:
    """Return CDS option NPV using Black on forward CDS spread."""
    cds, default_curve, discount_curve = _build_cds(evaluation_date, maturity_date, notional, running_spread, hazard_rate, discount_rate, buy_protection, frequency_months)
    eval_date = _as_date(evaluation_date)
    expiry = _as_future_date(expiry_date, eval_date, "expiry_date")
    vol = BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed())
    return BlackCdsOptionEngine(default_curve, _as_float(recovery_rate, "recovery_rate"), discount_curve, vol).calculate(
        CdsOption(option_type, expiry, _as_float(strike_spread, "strike_spread"), cds)
    ).value


@xw.func
def PYQUANTLIB_ZC_INFLATION_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    notional: float,
    fixed_rate: float,
    base_index: float,
    inflation_rate: float,
    discount_rate: float,
    receive_inflation: bool = True,
) -> float:
    """Return zero-coupon inflation swap NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    curve = ZeroInflationCurve(eval_date, _as_float(base_index, "base_index"), _as_float(inflation_rate, "inflation_rate"), Actual365Fixed())
    swap = ZeroCouponInflationSwap(
        SwapType.RECEIVER if _as_bool(_default_blank(receive_inflation, True), "receive_inflation") else SwapType.PAYER,
        _as_float(notional, "notional"),
        eval_date,
        maturity,
        _as_float(fixed_rate, "fixed_rate"),
        _as_float(base_index, "base_index"),
        Actual365Fixed(),
    )
    return DiscountingInflationSwapEngine(curve, FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed())).calculate_zero_coupon(swap).value


@xw.func
def PYQUANTLIB_YOY_INFLATION_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    notional: float,
    fixed_rate: float,
    base_index: float,
    inflation_rate: float,
    discount_rate: float,
    receive_inflation: bool = True,
    frequency_months: int = 12,
) -> float:
    """Return year-on-year inflation swap NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    schedule = Schedule.generate(eval_date, maturity, Period(_as_int(_default_blank(frequency_months, 12), "frequency_months"), TimeUnit.MONTHS), calendar=WeekendsOnly())
    curve = ZeroInflationCurve(eval_date, _as_float(base_index, "base_index"), _as_float(inflation_rate, "inflation_rate"), Actual365Fixed())
    swap = YearOnYearInflationSwap(
        SwapType.RECEIVER if _as_bool(_default_blank(receive_inflation, True), "receive_inflation") else SwapType.PAYER,
        _as_float(notional, "notional"),
        schedule,
        _as_float(fixed_rate, "fixed_rate"),
        _as_float(base_index, "base_index"),
        Actual365Fixed(),
    )
    return DiscountingInflationSwapEngine(curve, FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed())).calculate_year_on_year(swap).value


@xw.func
def PYQUANTLIB_VARIANCE_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    strike_variance: float,
    notional: float,
    volatility: float,
    discount_rate: float,
    long_position: bool = True,
) -> float:
    """Return variance swap NPV from a Black variance term structure."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    swap = VarianceSwap(_position_type(long_position), _as_float(strike_variance, "strike_variance"), _as_float(notional, "notional"), eval_date, maturity)
    return VarianceSwapEngine(
        BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed()),
    ).calculate(swap).value


@xw.func
def PYQUANTLIB_VOLATILITY_SWAP_NPV(
    evaluation_date: Any,
    maturity_date: Any,
    strike_volatility: float,
    notional: float,
    volatility: float,
    discount_rate: float,
    long_position: bool = True,
) -> float:
    """Return volatility swap NPV."""
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    swap = VolatilitySwap(_position_type(long_position), _as_float(strike_volatility, "strike_volatility"), _as_float(notional, "notional"), eval_date, maturity)
    return VolatilitySwapEngine(
        BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed()),
    ).calculate(swap).value


@xw.func
def PYQUANTLIB_FRA_NPV(
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
def PYQUANTLIB_FIXED_BOND_NPV(
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
def PYQUANTLIB_CAPFLOOR_NPV(
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
def PYQUANTLIB_SWAPTION_NPV(
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
def PYQUANTLIB_SWAP_NPV(
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
def PYQUANTLIB_SWAP_FAIR_RATE(
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


def _price_cms_swap(
    evaluation_date: Any,
    maturity_date: Any,
    nominal: float,
    fixed_rate: float,
    discount_rate: float,
    forward_rate: float,
    cms_tenor_months: int,
    pay_fixed: bool,
    frequency_months: int,
    spread: float,
    gearing: float,
    volatility: Any,
    discount_curve: Any = None,
    forward_curve: Any = None,
):
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    frequency = _as_int(_default_blank(frequency_months, 12), "frequency_months")
    cms_tenor = _as_int(_default_blank(cms_tenor_months, 60), "cms_tenor_months")
    calendar = WeekendsOnly()
    schedule = Schedule.generate(eval_date, maturity, Period(frequency, TimeUnit.MONTHS), calendar=calendar)
    discount_curve_obj = _build_curve(eval_date, discount_curve, discount_rate, "discount")
    forward_curve_obj = _build_curve(eval_date, forward_curve, forward_rate, "forward")
    vol = None if volatility in (None, "") else _build_swaption_vol(eval_date, volatility)
    swap = CmsSwap(
        SwapType.PAYER if _as_bool(_default_blank(pay_fixed, True), "pay_fixed") else SwapType.RECEIVER,
        _as_float(nominal, "nominal"),
        schedule,
        _as_float(fixed_rate, "fixed_rate"),
        Actual360(),
        schedule,
        Period(cms_tenor, TimeUnit.MONTHS),
        Actual360(),
        _as_float(_default_blank(spread, 0.0), "spread"),
        _as_float(_default_blank(gearing, 1.0), "gearing"),
    )
    return DiscountingCmsSwapEngine(discount_curve_obj, forward_curve_obj, vol).calculate(swap)


def _price_xccy_basis(
    evaluation_date: Any,
    maturity_date: Any,
    pay_nominal: float,
    receive_nominal: float,
    spot_fx: float,
    domestic_rate: float,
    foreign_rate: float,
    pay_spread: float,
    receive_spread: float,
    pay_leg_domestic: bool,
    frequency_months: int,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
):
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    frequency = _as_int(_default_blank(frequency_months, 6), "frequency_months")
    calendar = WeekendsOnly()
    schedule = Schedule.generate(eval_date, maturity, Period(frequency, TimeUnit.MONTHS), calendar=calendar)
    domestic_curve_obj = _build_curve(eval_date, domestic_curve, domestic_rate, "domestic")
    foreign_curve_obj = _build_curve(eval_date, foreign_curve, foreign_rate, "foreign")
    domestic_index = IborIndex("DOM-Ibor", Period(frequency, TimeUnit.MONTHS), 2, calendar, Actual360(), domestic_curve_obj)
    foreign_index = IborIndex("FOR-Ibor", Period(frequency, TimeUnit.MONTHS), 2, calendar, Actual360(), foreign_curve_obj)
    pay_domestic = _as_bool(_default_blank(pay_leg_domestic, True), "pay_leg_domestic")
    swap = CrossCurrencyBasisSwap(
        _as_float(pay_nominal, "pay_nominal"),
        "DOM" if pay_domestic else "FOR",
        schedule,
        domestic_index if pay_domestic else foreign_index,
        _as_float(_default_blank(pay_spread, 0.0), "pay_spread"),
        1.0,
        _as_float(receive_nominal, "receive_nominal"),
        "FOR" if pay_domestic else "DOM",
        schedule,
        foreign_index if pay_domestic else domestic_index,
        _as_float(_default_blank(receive_spread, 0.0), "receive_spread"),
        1.0,
    )
    engine = DiscountingCrossCurrencySwapEngine("DOM", domestic_curve_obj, "FOR", foreign_curve_obj, SimpleQuote(_as_float(spot_fx, "spot_fx")))
    return engine.calculate_basis_swap(swap)


def _price_xccy_fixed_float(
    evaluation_date: Any,
    maturity_date: Any,
    fixed_nominal: float,
    float_nominal: float,
    spot_fx: float,
    fixed_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    float_spread: float,
    pay_fixed: bool,
    fixed_leg_domestic: bool,
    frequency_months: int,
    domestic_curve: Any = None,
    foreign_curve: Any = None,
):
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    frequency = _as_int(_default_blank(frequency_months, 6), "frequency_months")
    calendar = WeekendsOnly()
    schedule = Schedule.generate(eval_date, maturity, Period(frequency, TimeUnit.MONTHS), calendar=calendar)
    domestic_curve_obj = _build_curve(eval_date, domestic_curve, domestic_rate, "domestic")
    foreign_curve_obj = _build_curve(eval_date, foreign_curve, foreign_rate, "foreign")
    fixed_domestic = _as_bool(_default_blank(fixed_leg_domestic, True), "fixed_leg_domestic")
    float_index = IborIndex(
        "Float-Ibor",
        Period(frequency, TimeUnit.MONTHS),
        2,
        calendar,
        Actual360(),
        foreign_curve_obj if fixed_domestic else domestic_curve_obj,
    )
    swap = CrossCurrencyFixedFloatSwap(
        SwapType.PAYER if _as_bool(_default_blank(pay_fixed, True), "pay_fixed") else SwapType.RECEIVER,
        _as_float(fixed_nominal, "fixed_nominal"),
        "DOM" if fixed_domestic else "FOR",
        schedule,
        _as_float(fixed_rate, "fixed_rate"),
        Actual360(),
        _as_float(float_nominal, "float_nominal"),
        "FOR" if fixed_domestic else "DOM",
        schedule,
        float_index,
        _as_float(_default_blank(float_spread, 0.0), "float_spread"),
    )
    engine = DiscountingCrossCurrencySwapEngine("DOM", domestic_curve_obj, "FOR", foreign_curve_obj, SimpleQuote(_as_float(spot_fx, "spot_fx")))
    return engine.calculate_fixed_float_swap(swap)


def _equity_exotic_engine(eval_date: date, spot: float, risk_free_rate: float, dividend_rate: float, volatility: float, paths: int):
    return McEquityExoticEngine(
        SimpleQuote(_as_float(spot, "spot")),
        FlatForwardCurve(eval_date, _as_float(dividend_rate, "dividend_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(risk_free_rate, "risk_free_rate"), Actual365Fixed()),
        BlackConstantVol(eval_date, _as_float(volatility, "volatility"), Actual365Fixed()),
        paths=_as_int(_default_blank(paths, 1024), "paths"),
    )


def _build_cds(
    evaluation_date: Any,
    maturity_date: Any,
    notional: float,
    running_spread: float,
    hazard_rate: float,
    discount_rate: float,
    buy_protection: bool,
    frequency_months: int,
):
    eval_date = _as_date(evaluation_date)
    maturity = _as_future_date(maturity_date, eval_date, "maturity_date")
    frequency = _as_int(_default_blank(frequency_months, 3), "frequency_months")
    schedule = Schedule.generate(eval_date, maturity, Period(frequency, TimeUnit.MONTHS), calendar=WeekendsOnly())
    cds = CreditDefaultSwap(
        ProtectionSide.BUYER if _as_bool(_default_blank(buy_protection, True), "buy_protection") else ProtectionSide.SELLER,
        _as_float(notional, "notional"),
        _as_float(running_spread, "running_spread"),
        schedule,
        Actual360(),
    )
    return (
        cds,
        FlatHazardRate(eval_date, _as_float(hazard_rate, "hazard_rate"), Actual365Fixed()),
        FlatForwardCurve(eval_date, _as_float(discount_rate, "discount_rate"), Actual365Fixed()),
    )


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
        if value.strip() and set(value.strip()) == {"#"}:
            raise ValueError(f"{name} contains Excel overflow text {value!r}; widen the cell or enter the vector as text such as 1000000;900000;800000;700000")
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


def _as_date_vector(value: Any, anchor: date, name: str) -> tuple[date, ...]:
    if value is None or value == "":
        raise ValueError(f"{name} is required")
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace("\n", ";").replace(",", ";").split(";") if piece.strip()]
    elif isinstance(value, (list, tuple)):
        pieces = []
        for item in value:
            if isinstance(item, (list, tuple)):
                pieces.extend(x for x in item if x not in (None, ""))
            elif item not in (None, ""):
                pieces.append(item)
    else:
        pieces = [value]
    dates = tuple(_as_future_date(item, anchor, name) for item in pieces)
    if not dates:
        raise ValueError(f"{name} contains no dates")
    return dates


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


def _position_type(value: Any) -> PositionType:
    if isinstance(value, PositionType):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in ("LONG", "L", "BUY", "TRUE", "T", "YES", "Y", "1"):
            return PositionType.LONG
        if normalized in ("SHORT", "S", "SELL", "FALSE", "F", "NO", "N", "0"):
            return PositionType.SHORT
    return PositionType.LONG if _as_bool(value, "long_position") else PositionType.SHORT


def _equity_barrier_direction(value: str) -> EquityBarrierDirection:
    normalized = str(value).strip().upper()
    if normalized in ("UP", "U"):
        return EquityBarrierDirection.UP
    if normalized in ("DOWN", "D"):
        return EquityBarrierDirection.DOWN
    raise ValueError("direction must be UP or DOWN")


def _equity_barrier_style(value: str) -> EquityBarrierStyle:
    normalized = str(value).strip().upper().replace("_", "").replace("-", "").replace(" ", "")
    if normalized in ("KNOCKOUT", "OUT", "KO"):
        return EquityBarrierStyle.KNOCK_OUT
    if normalized in ("KNOCKIN", "IN", "KI"):
        return EquityBarrierStyle.KNOCK_IN
    raise ValueError("style must be KNOCK_OUT or KNOCK_IN")
