from __future__ import annotations

import math
import unittest
from datetime import date

from pyqlite import (
    Actual360,
    Actual365Fixed,
    AnalyticFxOptionEngine,
    AnalyticDigitalFxOptionEngine,
    BlackCapFloorEngine,
    BlackConstantVol,
    BlackDeltaVolSurface,
    BlackSwaptionEngine,
    BlackVarianceSurface,
    BusinessDayConvention,
    BarrierDirection,
    BarrierFxOption,
    BarrierStyle,
    BasketFxOption,
    CliquetFxOption,
    DigitalFxOption,
    CapFloor,
    DiscountingBondEngine,
    DiscountingFraEngine,
    DiscountingFxForwardEngine,
    DiscountingSwapEngine,
    FixedRateBond,
    FloatFloatSwap,
    FlatForwardCurve,
    ForwardRateAgreement,
    ForwardStartFxOption,
    FxForward,
    FxOption,
    IborIndex,
    LookbackFxOption,
    McFxExoticEngine,
    NonstandardSwap,
    OptionType,
    OvernightIndexedSwap,
    Period,
    PositionType,
    QuantoFxOption,
    Schedule,
    SabrParameters,
    SabrSwaptionVolatilityCube,
    SimpleQuote,
    SwapType,
    Swaption,
    SwaptionVolatilityCube,
    SwaptionVolatilityMatrix,
    Thirty360,
    Thirty360Convention,
    TimeUnit,
    VanillaSwap,
    WeekendsOnly,
    ZeroCurve,
    DoubleBarrierFxOption,
    AsianFxOption,
    WindowBarrierFxOption,
)
from pyqlite.cashflows import ibor_leg
from pyqlite.math.black import black_formula
from pyqlite.math import AtmType, BlackDeltaCalculator, DeltaType


class PricingTests(unittest.TestCase):
    def test_vanilla_swap_fair_rate_reprices_to_zero(self) -> None:
        today = date(2026, 5, 22)
        calendar = WeekendsOnly()
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        schedule = Schedule.generate(
            today,
            date(2031, 5, 22),
            Period(6, TimeUnit.MONTHS),
            calendar=calendar,
        )
        index = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, calendar, Actual360(), curve)
        swap = VanillaSwap(
            SwapType.PAYER,
            1_000_000.0,
            schedule,
            0.03,
            Actual360(),
            schedule,
            index,
            0.0,
            Actual360(),
        )

        result = DiscountingSwapEngine(curve).calculate(swap)
        par_swap = VanillaSwap(
            SwapType.PAYER,
            1_000_000.0,
            schedule,
            result.fair_rate,
            Actual360(),
            schedule,
            index,
            0.0,
            Actual360(),
        )
        par_result = DiscountingSwapEngine(curve).calculate(par_swap)

        self.assertNotEqual(result.value, 0.0)
        self.assertAlmostEqual(par_result.value, 0.0, places=7)

    def test_fx_forward_discounting_engine(self) -> None:
        today = date(2026, 5, 22)
        maturity = date(2027, 5, 24)
        usd_curve = FlatForwardCurve(today, 0.04, Actual365Fixed())
        sgd_curve = FlatForwardCurve(today, 0.025, Actual365Fixed())
        spot = SimpleQuote(1.35)
        forward = FxForward.from_forward_rate(
            1_000_000.0,
            "USD",
            "SGD",
            1.36,
            maturity,
            pay_source_currency=True,
            settlement_calendar=WeekendsOnly(),
        )

        result = DiscountingFxForwardEngine(usd_curve, sgd_curve, spot).calculate(forward, today)
        settlement = forward.settlement_date(today)
        expected_df_usd = usd_curve.discount(maturity) / usd_curve.discount(settlement)
        expected_df_sgd = sgd_curve.discount(maturity) / sgd_curve.discount(settlement)
        expected_fair_fwd = spot.value * expected_df_sgd / expected_df_usd
        expected_zero_npv_fwd = spot.value * expected_df_usd / expected_df_sgd
        expected_value = -1_000_000.0 * expected_df_usd + 1_360_000.0 * expected_df_sgd / spot.value

        self.assertAlmostEqual(result.fair_forward_rate, expected_fair_fwd, places=12)
        self.assertAlmostEqual(result.zero_npv_forward_rate, expected_zero_npv_fwd, places=12)
        self.assertAlmostEqual(result.value, expected_value, places=8)

    def test_forward_rate_agreement_discounting(self) -> None:
        today = date(2026, 5, 22)
        value_date = date(2026, 11, 24)
        maturity = date(2027, 5, 24)
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        index = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, WeekendsOnly(), Actual360(), curve)
        fra = ForwardRateAgreement(index, value_date, maturity, PositionType.LONG, 0.0325, 1_000_000.0)

        result = DiscountingFraEngine(curve).calculate(fra, today)
        tau = Actual360().year_fraction(value_date, maturity)
        forward = (curve.discount(value_date) / curve.discount(maturity) - 1.0) / tau
        amount = 1_000_000.0 * (forward - 0.0325) * tau / (1.0 + forward * tau)

        self.assertAlmostEqual(result.forward_rate, forward, places=12)
        self.assertAlmostEqual(result.amount, amount, places=8)
        self.assertAlmostEqual(result.value, amount * curve.discount(value_date), places=8)

    def test_fixed_rate_bond_discounting(self) -> None:
        today = date(2026, 5, 22)
        curve = FlatForwardCurve(today, 0.04, Actual365Fixed())
        schedule = Schedule.generate(
            today,
            date(2029, 5, 22),
            Period(12, TimeUnit.MONTHS),
            calendar=WeekendsOnly(),
        )
        bond = FixedRateBond.from_schedule(2, 100.0, schedule, 0.05, Actual365Fixed(), payment_calendar=WeekendsOnly())

        result = DiscountingBondEngine(curve).calculate(bond, today)
        expected = sum(cf.amount * curve.discount(cf.payment_date) for cf in bond.cashflows if cf.payment_date > today)

        self.assertAlmostEqual(result.value, expected, places=12)
        self.assertGreater(result.settlement_value, 0.0)

    def test_black_cap_floor_engine_cap(self) -> None:
        today = date(2026, 5, 22)
        start = date(2026, 11, 24)
        maturity = date(2028, 11, 24)
        calendar = WeekendsOnly()
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        index = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, calendar, Actual360(), curve)
        schedule = Schedule.generate(start, maturity, Period(6, TimeUnit.MONTHS), calendar=calendar)
        leg = ibor_leg(schedule, 1_000_000.0, index, day_counter=Actual360())
        cap = CapFloor.cap(leg, (0.04,))
        vol = BlackConstantVol(today, 0.20, Actual365Fixed())

        result = BlackCapFloorEngine(curve, vol).calculate(cap)
        expected = 0.0
        for coupon in leg:
            forward = index.fixing(coupon.fixing_date, coupon.accrual_start_date, coupon.accrual_end_date)
            discount = curve.discount(coupon.payment_date)
            stddev = math.sqrt(vol.black_variance(coupon.fixing_date, 0.04))
            expected += black_formula(
                1,
                forward,
                0.04,
                stddev,
                discount * coupon.nominal * coupon.gearing * coupon.accrual_period,
            ).value

        self.assertAlmostEqual(result.value, expected, places=8)
        self.assertGreater(result.vega, 0.0)

    def test_black_swaption_engine_physical_european(self) -> None:
        today = date(2026, 5, 22)
        exercise = date(2027, 5, 24)
        maturity = date(2032, 5, 24)
        calendar = WeekendsOnly()
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        schedule = Schedule.generate(exercise, maturity, Period(6, TimeUnit.MONTHS), calendar=calendar)
        index = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, calendar, Actual360(), curve)
        swap = VanillaSwap(
            SwapType.PAYER,
            1_000_000.0,
            schedule,
            0.0375,
            Actual360(),
            schedule,
            index,
            0.0,
            Actual360(),
        )
        vol = BlackConstantVol(today, 0.18, Actual365Fixed())

        result = BlackSwaptionEngine(curve, vol).calculate(Swaption(swap, exercise))
        swap_result = DiscountingSwapEngine(curve, include_settlement_date_flows=False).calculate(swap)
        annuity = abs(swap_result.fixed_leg_bps) / 1.0e-4
        stddev = math.sqrt(vol.black_variance(exercise, swap.fixed_rate))
        expected = black_formula(1, swap_result.fair_rate, swap.fixed_rate, stddev, annuity).value

        self.assertAlmostEqual(result.value, expected, places=8)
        self.assertGreater(result.vega, 0.0)

    def test_swaption_volatility_matrix_is_used_by_engine(self) -> None:
        today = date(2026, 5, 22)
        exercise = date(2027, 5, 24)
        maturity = date(2032, 5, 24)
        calendar = WeekendsOnly()
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        schedule = Schedule.generate(exercise, maturity, Period(6, TimeUnit.MONTHS), calendar=calendar)
        index = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, calendar, Actual360(), curve)
        swap = VanillaSwap(
            SwapType.PAYER,
            1_000_000.0,
            schedule,
            0.0375,
            Actual360(),
            schedule,
            index,
            0.0,
            Actual360(),
        )
        matrix = SwaptionVolatilityMatrix(
            today,
            (Period(1, TimeUnit.YEARS), Period(2, TimeUnit.YEARS)),
            (Period(5, TimeUnit.YEARS), Period(10, TimeUnit.YEARS)),
            ((0.18, 0.19), (0.20, 0.21)),
        )

        result = BlackSwaptionEngine(curve, matrix).calculate(Swaption(swap, exercise))
        const_result = BlackSwaptionEngine(curve, BlackConstantVol(today, 0.18, Actual365Fixed())).calculate(Swaption(swap, exercise))

        self.assertGreater(result.value, 0.0)
        self.assertNotAlmostEqual(result.value, const_result.value, places=2)

    def test_swaption_volatility_cube_and_sabr_smile(self) -> None:
        today = date(2026, 5, 22)
        exercise = date(2027, 5, 24)
        maturity = date(2032, 5, 24)
        calendar = WeekendsOnly()
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        schedule = Schedule.generate(exercise, maturity, Period(6, TimeUnit.MONTHS), calendar=calendar)
        index = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, calendar, Actual360(), curve)
        swap = VanillaSwap(
            SwapType.PAYER,
            1_000_000.0,
            schedule,
            0.045,
            Actual360(),
            schedule,
            index,
            0.0,
            Actual360(),
        )
        matrix = SwaptionVolatilityMatrix(
            today,
            (Period(1, TimeUnit.YEARS), Period(2, TimeUnit.YEARS)),
            (Period(5, TimeUnit.YEARS), Period(10, TimeUnit.YEARS)),
            ((0.18, 0.19), (0.20, 0.21)),
        )
        cube = SwaptionVolatilityCube(
            matrix,
            (-0.01, 0.0, 0.01),
            (
                ((0.015, 0.014), (0.013, 0.012)),
                ((0.0, 0.0), (0.0, 0.0)),
                ((0.010, 0.011), (0.012, 0.013)),
            ),
        )
        sabr = SabrSwaptionVolatilityCube(
            matrix,
            (
                (SabrParameters(0.03, 0.5, 0.40, -0.20), SabrParameters(0.032, 0.5, 0.38, -0.18)),
                (SabrParameters(0.034, 0.5, 0.36, -0.16), SabrParameters(0.036, 0.5, 0.34, -0.14)),
            ),
        )

        cube_result = BlackSwaptionEngine(curve, cube).calculate(Swaption(swap, exercise))
        sabr_result = BlackSwaptionEngine(curve, sabr).calculate(Swaption(swap, exercise))

        self.assertGreater(cube_result.value, 0.0)
        self.assertGreater(sabr_result.value, 0.0)
        self.assertNotAlmostEqual(cube_result.value, sabr_result.value, places=2)

    def test_overnight_indexed_swap_fair_rate_reprices_to_zero(self) -> None:
        today = date(2026, 5, 22)
        calendar = WeekendsOnly()
        curve = FlatForwardCurve(today, 0.035, Actual365Fixed())
        schedule = Schedule.generate(today, date(2028, 5, 22), Period(12, TimeUnit.MONTHS), calendar=calendar)
        overnight = IborIndex("SOFR", Period(1, TimeUnit.DAYS), 0, calendar, Actual360(), curve)
        ois = OvernightIndexedSwap.from_nominal(SwapType.PAYER, 1_000_000.0, schedule, 0.03, Actual360(), overnight)

        result = DiscountingSwapEngine(curve).calculate(ois)
        par_ois = OvernightIndexedSwap.from_nominal(SwapType.PAYER, 1_000_000.0, schedule, result.fair_rate, Actual360(), overnight)
        par_result = DiscountingSwapEngine(curve).calculate(par_ois)

        self.assertAlmostEqual(par_result.value, 0.0, places=7)

    def test_float_float_and_nonstandard_swap_discounting(self) -> None:
        today = date(2026, 5, 22)
        calendar = WeekendsOnly()
        discount = FlatForwardCurve(today, 0.035, Actual365Fixed())
        curve3m = FlatForwardCurve(today, 0.034, Actual365Fixed())
        curve6m = FlatForwardCurve(today, 0.037, Actual365Fixed())
        schedule3m = Schedule.generate(today, date(2028, 5, 22), Period(3, TimeUnit.MONTHS), calendar=calendar)
        schedule6m = Schedule.generate(today, date(2028, 5, 22), Period(6, TimeUnit.MONTHS), calendar=calendar)
        index3m = IborIndex("USD-LIBOR-3M", Period(3, TimeUnit.MONTHS), 2, calendar, Actual360(), curve3m)
        index6m = IborIndex("USD-LIBOR-6M", Period(6, TimeUnit.MONTHS), 2, calendar, Actual360(), curve6m)
        basis = FloatFloatSwap.from_nominals(
            SwapType.PAYER,
            1_000_000.0,
            1_000_000.0,
            schedule3m,
            index3m,
            Actual360(),
            schedule6m,
            index6m,
            Actual360(),
            spread1=0.001,
        )

        basis_result = DiscountingSwapEngine(discount).calculate(basis)
        fixed_schedule = schedule6m
        nonstandard = NonstandardSwap(
            SwapType.PAYER,
            (1_000_000.0, 900_000.0, 800_000.0, 700_000.0),
            (1_000_000.0, 900_000.0, 800_000.0, 700_000.0),
            fixed_schedule,
            (0.03, 0.031, 0.032, 0.033),
            Actual360(),
            fixed_schedule,
            index6m,
            (1.0, 1.0, 1.0, 1.0),
            (0.0, 0.0, 0.0, 0.0),
            Actual360(),
            intermediate_capital_exchange=True,
            final_capital_exchange=True,
        )
        nonstandard_result = DiscountingSwapEngine(discount).calculate(nonstandard)

        self.assertNotEqual(basis_result.value, 0.0)
        self.assertNotEqual(nonstandard_result.value, 0.0)
        self.assertGreater(len(nonstandard.fixed_leg), len(nonstandard.fixed_nominal))

    def test_digital_fx_option_analytic(self) -> None:
        today = date(2026, 5, 22)
        expiry = date(2027, 5, 22)
        domestic = FlatForwardCurve(today, 0.04, Actual365Fixed())
        foreign = FlatForwardCurve(today, 0.02, Actual365Fixed())
        vol = BlackConstantVol(today, 0.15, Actual365Fixed())
        option = DigitalFxOption(OptionType.CALL, 1_000_000.0, 1.27, 1.0, expiry)

        result = AnalyticDigitalFxOptionEngine(SimpleQuote(1.25), domestic, foreign, vol).calculate(option)
        t = Actual365Fixed().year_fraction(today, expiry)
        domestic_df = math.exp(-0.04 * t)
        foreign_df = math.exp(-0.02 * t)
        forward = 1.25 * foreign_df / domestic_df
        stddev = 0.15 * math.sqrt(t)
        d2 = math.log(forward / 1.27) / stddev - 0.5 * stddev
        cdf = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

        self.assertAlmostEqual(result.value, 1_000_000.0 * domestic_df * cdf(d2), places=8)

    def test_mc_fx_exotic_products_smoke(self) -> None:
        today = date(2026, 5, 22)
        expiry = date(2027, 5, 22)
        domestic = FlatForwardCurve(today, 0.04, Actual365Fixed())
        foreign = FlatForwardCurve(today, 0.02, Actual365Fixed())
        vol = BlackConstantVol(today, 0.15, Actual365Fixed())
        engine = McFxExoticEngine(SimpleQuote(1.25), domestic, foreign, vol, paths=512, steps=32, seed=7)

        barrier = engine.calculate_barrier(
            BarrierFxOption(OptionType.CALL, 1_000_000.0, 1.20, 1.45, BarrierDirection.UP, BarrierStyle.KNOCK_OUT, expiry)
        )
        double_no_touch = engine.calculate_double_barrier(
            DoubleBarrierFxOption(1_000_000.0, 1.05, 1.45, expiry, 1.0)
        )
        asian = engine.calculate_asian(AsianFxOption(OptionType.CALL, 1_000_000.0, 1.20, expiry))
        window = engine.calculate_window_barrier(
            WindowBarrierFxOption(OptionType.CALL, 1_000_000.0, 1.20, 1.45, BarrierDirection.UP, BarrierStyle.KNOCK_OUT, date(2026, 8, 22), date(2026, 11, 22), expiry)
        )
        forward_start = engine.calculate_forward_start(
            ForwardStartFxOption(OptionType.CALL, 1_000_000.0, 1.0, date(2026, 11, 22), expiry)
        )
        quanto = engine.calculate_quanto(
            QuantoFxOption(OptionType.CALL, 1_000_000.0, 1.20, expiry, quanto_fx_rate=0.75, quanto_drift_adjustment=-0.01)
        )
        lookback = engine.calculate_lookback(LookbackFxOption(OptionType.CALL, 1_000_000.0, 1.20, expiry))
        cliquet = engine.calculate_cliquet(
            CliquetFxOption(1_000_000.0, (date(2026, 8, 22), date(2026, 11, 22), date(2027, 2, 22), expiry), -0.05, 0.05)
        )
        basket = engine.calculate_basket(
            BasketFxOption(
                OptionType.CALL,
                (1.25, 1.10),
                (foreign.discount(expiry), foreign.discount(expiry)),
                (0.15, 0.12),
                ((1.0, 0.35), (0.35, 1.0)),
                (0.5, 0.5),
                1.15,
                1_000_000.0,
                expiry,
            )
        )

        for result in (barrier, double_no_touch, asian, window, forward_start, quanto, lookback, basket):
            self.assertGreater(result.value, 0.0)
            self.assertGreater(result.paths, 0)
        self.assertNotEqual(cliquet.value, 0.0)

    def test_thirty360_quantlib_conventions(self) -> None:
        start = date(2021, 2, 28)
        end = date(2021, 3, 31)

        self.assertEqual(Thirty360(Thirty360Convention.USA).day_count(start, end), 30)
        self.assertEqual(Thirty360(Thirty360Convention.BOND_BASIS).day_count(start, end), 33)
        self.assertEqual(Thirty360(Thirty360Convention.EUROPEAN).day_count(start, end), 32)

    def test_calendar_advance_business_end_of_month(self) -> None:
        calendar = WeekendsOnly()

        result = calendar.advance(
            date(2021, 1, 29),
            Period(1, TimeUnit.MONTHS),
            BusinessDayConvention.MODIFIED_FOLLOWING,
            end_of_month_flag=True,
        )

        self.assertEqual(result, date(2021, 2, 26))

    def test_fx_option_garman_kohlhagen_call(self) -> None:
        today = date(2026, 5, 22)
        expiry = date(2027, 5, 22)
        domestic = FlatForwardCurve(today, 0.04, Actual365Fixed())
        foreign = FlatForwardCurve(today, 0.02, Actual365Fixed())
        vol = BlackConstantVol(today, 0.15, Actual365Fixed())
        spot = SimpleQuote(1.25)
        option = FxOption(OptionType.CALL, "USD", "EUR", 1_000_000.0, 1.27, expiry)

        result = AnalyticFxOptionEngine(spot, domestic, foreign, vol).calculate(option)
        t = Actual365Fixed().year_fraction(today, expiry)
        domestic_df = math.exp(-0.04 * t)
        foreign_df = math.exp(-0.02 * t)
        forward = spot.value * foreign_df / domestic_df
        stddev = 0.15 * math.sqrt(t)
        d1 = math.log(forward / 1.27) / stddev + 0.5 * stddev
        d2 = d1 - stddev
        cdf = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
        expected = 1_000_000.0 * domestic_df * (forward * cdf(d1) - 1.27 * cdf(d2))

        self.assertAlmostEqual(result.forward, forward, places=12)
        self.assertAlmostEqual(result.value, expected, places=8)
        self.assertGreater(result.vega, 0.0)

    def test_dated_zero_curves_and_vol_surface_price_fx_option(self) -> None:
        today = date(2026, 5, 22)
        expiry = date(2028, 5, 22)
        domestic = ZeroCurve(
            today,
            (date(2027, 5, 22), date(2029, 5, 22)),
            (0.039, 0.041),
            Actual365Fixed(),
        )
        foreign = ZeroCurve(
            today,
            (date(2027, 5, 22), date(2029, 5, 22)),
            (0.024, 0.027),
            Actual365Fixed(),
        )
        vol = BlackVarianceSurface(
            today,
            (date(2027, 5, 22), date(2029, 5, 22)),
            (1.10, 1.25, 1.40),
            ((0.17, 0.15, 0.16), (0.19, 0.165, 0.18)),
            Actual365Fixed(),
        )
        option = FxOption(OptionType.CALL, "USD", "EUR", 1_000_000.0, 1.27, expiry)

        result = AnalyticFxOptionEngine(SimpleQuote(1.25), domestic, foreign, vol).calculate(option)

        self.assertGreater(result.value, 0.0)
        self.assertGreater(result.vega, 0.0)
        self.assertNotAlmostEqual(vol.black_vol(expiry, 1.27), 0.15, places=3)

    def test_black_delta_calculator_spot_delta_strike_roundtrip(self) -> None:
        calc = BlackDeltaCalculator(
            1,
            DeltaType.SPOT,
            spot=1.25,
            domestic_discount=0.96,
            foreign_discount=0.98,
            stddev=0.20,
        )

        strike = calc.strike_from_delta(0.25)

        self.assertAlmostEqual(calc.delta_from_strike(strike), 0.25, places=9)
        self.assertGreater(calc.atm_strike(AtmType.ATM_DELTA_NEUTRAL), 0.0)

    def test_fx_delta_vol_surface_prices_option(self) -> None:
        today = date(2026, 5, 22)
        expiry = date(2028, 5, 22)
        domestic = ZeroCurve(
            today,
            (date(2027, 5, 22), date(2029, 5, 22)),
            (0.039, 0.041),
            Actual365Fixed(),
        )
        foreign = ZeroCurve(
            today,
            (date(2027, 5, 22), date(2029, 5, 22)),
            (0.024, 0.027),
            Actual365Fixed(),
        )
        vol = BlackDeltaVolSurface(
            today,
            (date(2027, 5, 22), date(2029, 5, 22)),
            (-0.25,),
            (0.25,),
            True,
            ((0.17, 0.15, 0.16), (0.19, 0.165, 0.18)),
            1.25,
            domestic,
            foreign,
            Actual365Fixed(),
            DeltaType.SPOT,
        )
        option = FxOption(OptionType.CALL, "USD", "EUR", 1_000_000.0, 1.27, expiry)

        result = AnalyticFxOptionEngine(SimpleQuote(1.25), domestic, foreign, vol).calculate(option)

        self.assertGreater(result.value, 0.0)
        self.assertGreater(vol.black_vol(expiry, 1.27), 0.0)


if __name__ == "__main__":
    unittest.main()
