# pyquantlib

`pyquantlib` is a standalone, standard-library-only Python pricing kernel for a deliberately small front-office scope:

- vanilla fixed-vs-floating interest-rate swaps
- overnight indexed swaps, float-float/basis swaps, and nonstandard amortizing swaps
- forward-rate agreements
- fixed-rate and zero-coupon bonds
- Black caps, floors, and collars
- physical European swaptions under Black 76
- Bermudan swaptions with a Longstaff-Schwartz swap-rate Monte Carlo engine
- CMS swaps with CMS forward rates and swaption-vol convexity adjustment
- constant-notional cross-currency basis and fixed-vs-floating swaps
- FX forwards
- European FX vanilla and digital options under Garman-Kohlhagen
- FX barrier, double-barrier/no-touch, Asian, window barrier, forward-start, quanto, lookback, cliquet, and basket/correlation option objects with deterministic Monte Carlo engines
- CDS and CDS options using flat/supplied default probability curves
- European equity options and equity total-return swaps
- equity barrier, Asian, lookback, cliquet, forward-start, and basket options
- commodity forwards, swaps, and European options
- zero-coupon and year-on-year inflation swaps
- variance and volatility swaps

It does not import, link, wrap, or require the C++ QuantLib library. The package is organized around independent Python modules for dates, calendars, schedules, day counters, curves, volatility, cashflows, instruments, and pricing engines.

## Quick Example

```python
from datetime import date

from pyquantlib import (
    Actual365Fixed,
    DiscountingFxForwardEngine,
    FlatForwardCurve,
    FxForward,
    SimpleQuote,
    WeekendsOnly,
)

today = date(2026, 5, 22)
maturity = date(2027, 5, 24)

usd_curve = FlatForwardCurve(today, 0.04, Actual365Fixed())
sgd_curve = FlatForwardCurve(today, 0.025, Actual365Fixed())
spot = SimpleQuote(1.35)

trade = FxForward.from_forward_rate(
    1_000_000.0,
    "USD",
    "SGD",
    1.36,
    maturity,
    pay_source_currency=True,
    settlement_calendar=WeekendsOnly(),
)

result = DiscountingFxForwardEngine(usd_curve, sgd_curve, spot).calculate(trade, today)
print(result.value, result.fair_forward_rate, result.zero_npv_forward_rate)
```

## Development Checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
env PYTHONPYCACHEPREFIX=/private/tmp/pyquantlib-pyc python3 -m compileall -q pyquantlib pyquantlib_xlwings tests examples/pyquantlib_workbook.py
```

## Excel Usage With xlwings

The package includes a thin `pyquantlib_xlwings` wrapper for xlwings. `pyquantlib` remains the standalone pricing library; `pyquantlib_xlwings` only adapts selected functions to Excel.

Install the package, including the optional Excel dependency, into the Python environment used by Excel:

```bash
python -m pip install "/path/to/pyquantlib_standalone[excel]"
```

Install the xlwings Excel add-in:

```bash
xlwings addin install
```

### Option 1: Worksheet Functions

On Windows, open-source xlwings supports Python UDF worksheet functions. In the xlwings ribbon, set:

```text
PYTHONPATH: /path/to/pyquantlib_standalone
UDF Modules: pyquantlib_xlwings.functions
```

Then click `Import Python UDFs`. The following worksheet functions become available:

```text
PYQUANTLIB_FX_FORWARD_RATE(evaluation_date, maturity_date, spot_fx, source_rate, target_rate, settlement_days)
PYQUANTLIB_FX_FORWARD_ZERO_NPV_RATE(evaluation_date, maturity_date, spot_fx, source_rate, target_rate, settlement_days)
PYQUANTLIB_FX_FORWARD_NPV(evaluation_date, maturity_date, spot_fx, source_nominal, contract_forward_rate, source_rate, target_rate, pay_source_currency, settlement_days)
PYQUANTLIB_FX_OPTION_NPV(option_type, evaluation_date, expiry_date, spot_fx, strike, foreign_notional, domestic_rate, foreign_rate, volatility)
PYQUANTLIB_DIGITAL_FX_OPTION_NPV(option_type, evaluation_date, expiry_date, spot_fx, strike, notional, cash_payoff, domestic_rate, foreign_rate, volatility)
PYQUANTLIB_FRA_NPV(evaluation_date, value_date, maturity_date, notional, strike_rate, forward_rate, discount_rate, long_position, settlement_days)
PYQUANTLIB_FIXED_BOND_NPV(evaluation_date, maturity_date, face_amount, coupon_rate, discount_rate, frequency_months, settlement_days)
PYQUANTLIB_CAPFLOOR_NPV(cap_floor_type, evaluation_date, start_date, maturity_date, notional, cap_rate, floor_rate, forward_rate, discount_rate, volatility, frequency_months)
PYQUANTLIB_SWAPTION_NPV(evaluation_date, exercise_date, maturity_date, nominal, fixed_rate, discount_rate, forward_rate, volatility, pay_fixed)
PYQUANTLIB_SWAP_NPV(evaluation_date, maturity_date, nominal, fixed_rate, discount_rate, forward_rate, pay_fixed, fixed_frequency_months, floating_frequency_months, floating_spread)
PYQUANTLIB_SWAP_FAIR_RATE(evaluation_date, maturity_date, nominal, discount_rate, forward_rate, pay_fixed, fixed_frequency_months, floating_frequency_months, floating_spread)
PYQUANTLIB_BERMUDAN_SWAPTION_NPV(evaluation_date, exercise_dates, maturity_date, nominal, fixed_rate, discount_rate, forward_rate, volatility, pay_fixed)
PYQUANTLIB_OIS_NPV(evaluation_date, maturity_date, nominal, fixed_rate, discount_rate, overnight_rate, pay_fixed, frequency_months, floating_spread)
PYQUANTLIB_OIS_FAIR_RATE(evaluation_date, maturity_date, nominal, discount_rate, overnight_rate, pay_fixed, frequency_months, floating_spread)
PYQUANTLIB_FLOAT_FLOAT_NPV(evaluation_date, maturity_date, nominal1, nominal2, discount_rate, forward_rate1, forward_rate2, spread1, spread2, pay_leg1, frequency1_months, frequency2_months)
PYQUANTLIB_NONSTANDARD_SWAP_NPV(evaluation_date, maturity_date, fixed_nominals, floating_nominals, fixed_rates, discount_rate, forward_rate, pay_fixed, frequency_months, gearings, spreads, intermediate_capital_exchange, final_capital_exchange)
PYQUANTLIB_CMS_SWAP_NPV(evaluation_date, maturity_date, nominal, fixed_rate, discount_rate, forward_rate, cms_tenor_months, pay_fixed)
PYQUANTLIB_CMS_SWAP_FAIR_RATE(evaluation_date, maturity_date, nominal, discount_rate, forward_rate, cms_tenor_months, pay_fixed)
PYQUANTLIB_XCCY_BASIS_SWAP_NPV(evaluation_date, maturity_date, pay_nominal, receive_nominal, spot_fx, domestic_rate, foreign_rate, pay_spread, receive_spread)
PYQUANTLIB_XCCY_BASIS_SWAP_FAIR_PAY_SPREAD(evaluation_date, maturity_date, pay_nominal, receive_nominal, spot_fx, domestic_rate, foreign_rate, pay_spread, receive_spread)
PYQUANTLIB_XCCY_FIXED_FLOAT_NPV(evaluation_date, maturity_date, fixed_nominal, float_nominal, spot_fx, fixed_rate, domestic_rate, foreign_rate, float_spread)
PYQUANTLIB_EQUITY_OPTION_NPV(option_type, evaluation_date, expiry_date, spot, strike, quantity, risk_free_rate, dividend_rate, volatility)
PYQUANTLIB_EQUITY_BARRIER_OPTION_NPV(option_type, evaluation_date, expiry_date, spot, strike, quantity, barrier, direction, style, risk_free_rate, dividend_rate, volatility)
PYQUANTLIB_EQUITY_ASIAN_OPTION_NPV(option_type, evaluation_date, expiry_date, spot, strike, quantity, risk_free_rate, dividend_rate, volatility)
PYQUANTLIB_EQUITY_TRS_NPV(evaluation_date, maturity_date, notional, spot, initial_price, risk_free_rate, dividend_rate, funding_rate, funding_spread)
PYQUANTLIB_COMMODITY_FORWARD_NPV(evaluation_date, maturity_date, spot, quantity, contract_price, forward_rate, discount_rate, long_position)
PYQUANTLIB_COMMODITY_SWAP_NPV(evaluation_date, maturity_date, spot, quantity, fixed_price, forward_rate, discount_rate, receive_floating)
PYQUANTLIB_COMMODITY_OPTION_NPV(option_type, evaluation_date, expiry_date, spot, quantity, strike, forward_rate, discount_rate, volatility)
PYQUANTLIB_CDS_NPV(evaluation_date, maturity_date, notional, running_spread, hazard_rate, recovery_rate, discount_rate, buy_protection)
PYQUANTLIB_CDS_OPTION_NPV(option_type, evaluation_date, expiry_date, maturity_date, notional, running_spread, strike_spread, hazard_rate, recovery_rate, discount_rate, volatility)
PYQUANTLIB_ZC_INFLATION_SWAP_NPV(evaluation_date, maturity_date, notional, fixed_rate, base_index, inflation_rate, discount_rate, receive_inflation)
PYQUANTLIB_YOY_INFLATION_SWAP_NPV(evaluation_date, maturity_date, notional, fixed_rate, base_index, inflation_rate, discount_rate, receive_inflation)
PYQUANTLIB_VARIANCE_SWAP_NPV(evaluation_date, maturity_date, strike_variance, notional, volatility, discount_rate, long_position)
PYQUANTLIB_VOLATILITY_SWAP_NPV(evaluation_date, maturity_date, strike_volatility, notional, volatility, discount_rate, long_position)
```

Example Excel formulas:

```text
=PYQUANTLIB_FX_FORWARD_RATE(DATE(2026,5,22),DATE(2027,5,24),1.35,0.04,0.025,2)
=PYQUANTLIB_FX_FORWARD_ZERO_NPV_RATE(DATE(2026,5,22),DATE(2027,5,24),1.35,0.04,0.025,2)
=PYQUANTLIB_FX_FORWARD_NPV(DATE(2026,5,22),DATE(2027,5,24),1.35,1000000,1.36,0.04,0.025,TRUE,2)
=PYQUANTLIB_FX_OPTION_NPV("CALL",DATE(2026,5,22),DATE(2027,5,22),1.25,1.27,1000000,0.04,0.02,0.15)
=PYQUANTLIB_DIGITAL_FX_OPTION_NPV("CALL",DATE(2026,5,22),DATE(2027,5,22),1.25,1.27,1000000,1,0.04,0.02,0.15)
=PYQUANTLIB_FRA_NPV(DATE(2026,5,22),DATE(2026,11,24),DATE(2027,5,24),1000000,0.0325,0.035,0.035,TRUE,2)
=PYQUANTLIB_FIXED_BOND_NPV(DATE(2026,5,22),DATE(2029,5,22),100,0.05,0.04,12,2)
=PYQUANTLIB_CAPFLOOR_NPV("CAP",DATE(2026,5,22),DATE(2026,11,24),DATE(2028,11,24),1000000,0.04,"",0.035,0.035,0.20,6)
=PYQUANTLIB_SWAPTION_NPV(DATE(2026,5,22),DATE(2027,5,24),DATE(2032,5,24),1000000,0.0375,0.035,0.035,0.18,TRUE)
=PYQUANTLIB_SWAPTION_NPV(DATE(2026,5,22),DATE(2027,5,24),DATE(2032,5,24),1000000,0.0375,0.035,0.035,"matrix|1Y,2Y|5Y,10Y|0.18,0.19;0.20,0.21",TRUE)
=PYQUANTLIB_BERMUDAN_SWAPTION_NPV(DATE(2026,5,22),"2027-05-24,2028-05-24,2029-05-24",DATE(2032,5,24),1000000,0.0375,0.035,0.036,0.18,TRUE)
=PYQUANTLIB_SWAP_FAIR_RATE(DATE(2026,5,22),DATE(2031,5,22),1000000,0.035,0.035,TRUE,6,6,0)
=PYQUANTLIB_SWAP_NPV(DATE(2026,5,22),DATE(2031,5,22),1000000,0.03,0.035,0.035,TRUE,6,6,0)
=PYQUANTLIB_OIS_FAIR_RATE(DATE(2026,5,22),DATE(2031,5,22),1000000,0.035,0.034,TRUE,12,0)
=PYQUANTLIB_OIS_NPV(DATE(2026,5,22),DATE(2031,5,22),1000000,0.034,0.035,0.034,TRUE,12,0)
=PYQUANTLIB_FLOAT_FLOAT_NPV(DATE(2026,5,22),DATE(2031,5,22),1000000,1000000,0.035,0.033,0.036,0,0.001,TRUE,3,6)
=PYQUANTLIB_NONSTANDARD_SWAP_NPV(DATE(2026,5,22),DATE(2028,5,22),"1000000,900000,800000,700000","1000000,900000,800000,700000","0.033,0.034,0.035,0.036",0.035,0.034,TRUE,6,"1,1,1,1","0.001,0.001,0.001,0.001",TRUE,TRUE)
=PYQUANTLIB_CMS_SWAP_FAIR_RATE(DATE(2026,5,22),DATE(2031,5,22),1000000,0.035,0.037,60,TRUE)
=PYQUANTLIB_XCCY_BASIS_SWAP_NPV(DATE(2026,5,22),DATE(2029,5,22),1000000,900000,1.10,0.04,0.025,0.001,0.002)
=PYQUANTLIB_EQUITY_BARRIER_OPTION_NPV("CALL",DATE(2026,5,22),DATE(2027,5,22),100,100,1000,130,"UP","KNOCK_OUT",0.04,0.015,0.22)
=PYQUANTLIB_COMMODITY_OPTION_NPV("CALL",DATE(2026,5,22),DATE(2027,5,22),80,1000,82,0.02,0.04,0.25)
=PYQUANTLIB_CDS_NPV(DATE(2026,5,22),DATE(2031,5,22),1000000,0.01,0.018,0.4,0.035,TRUE)
=PYQUANTLIB_ZC_INFLATION_SWAP_NPV(DATE(2026,5,22),DATE(2031,5,22),1000000,0.02,250,0.025,0.035,TRUE)
=PYQUANTLIB_VARIANCE_SWAP_NPV(DATE(2026,5,22),DATE(2027,5,22),0.04,1000000,0.25,0.04,TRUE)
```

### Option 2: RunPython Sheet Workflow

For Windows or macOS, xlwings supports running Python from Excel through the xlwings add-in. You can call:

```python
pyquantlib_xlwings.runpython.price_active_sheet
```

The active sheet should have headers on row 1. Required common headers:

```text
product, output, evaluation_date, maturity_date
```

Use `product` values:

```text
FX_FORWARD_RATE
FX_FORWARD_ZERO_NPV_RATE
FX_FORWARD_NPV
FX_OPTION_NPV
DIGITAL_FX_OPTION_NPV
FRA_NPV
FIXED_BOND_NPV
CAPFLOOR_NPV
SWAPTION_NPV
BERMUDAN_SWAPTION_NPV
SWAP_FAIR_RATE
SWAP_NPV
OIS_NPV
OIS_FAIR_RATE
FLOAT_FLOAT_NPV
NONSTANDARD_SWAP_NPV
CMS_SWAP_NPV
CMS_SWAP_FAIR_RATE
XCCY_BASIS_SWAP_NPV
XCCY_BASIS_SWAP_FAIR_PAY_SPREAD
XCCY_FIXED_FLOAT_NPV
EQUITY_OPTION_NPV
EQUITY_BARRIER_OPTION_NPV
EQUITY_ASIAN_OPTION_NPV
EQUITY_TRS_NPV
COMMODITY_FORWARD_NPV
COMMODITY_SWAP_NPV
COMMODITY_OPTION_NPV
CDS_NPV
CDS_OPTION_NPV
ZC_INFLATION_SWAP_NPV
YOY_INFLATION_SWAP_NPV
VARIANCE_SWAP_NPV
VOLATILITY_SWAP_NPV
```

Additional headers used by the supported products:

```text
spot_fx, source_nominal, contract_forward_rate, source_rate, target_rate,
pay_source_currency, option_type, strike, foreign_notional, domestic_rate,
foreign_rate, volatility, nominal, fixed_rate, discount_rate, forward_rate,
pay_fixed, value_date, start_date, exercise_date, notional, strike_rate,
long_position, face_amount, coupon_rate, frequency_months, cap_floor_type,
cap_rate, floor_rate, overnight_rate, cash_payoff, nominal1, nominal2,
forward_rate1, forward_rate2, spread1, spread2, pay_leg1, frequency1_months,
frequency2_months, fixed_nominals, floating_nominals, fixed_rates, gearings,
spreads, intermediate_capital_exchange, final_capital_exchange,
exercise_dates, cms_tenor_months, spread, gearing, paths, pay_nominal,
receive_nominal, pay_spread, receive_spread, pay_leg_domestic, fixed_nominal,
float_nominal, float_spread, fixed_leg_domestic, spot, quantity,
risk_free_rate, dividend_rate, barrier, barrier_direction, barrier_style,
initial_price, funding_rate, funding_spread, contract_price, fixed_price,
receive_floating, running_spread, hazard_rate, recovery_rate, buy_protection,
strike_spread, base_index, inflation_rate, receive_inflation,
strike_variance, strike_volatility
```

Rows are priced from row 2 downward until the first blank `product` cell. Results are written into the `output` column.

`FX_FORWARD_RATE` follows QuantLib's `DiscountingFxForwardEngine::fairForwardRate`
result exactly. For a contract rate that makes the `FX_FORWARD_NPV` row zero
under the wrapper's pay-source-currency convention, use
`FX_FORWARD_ZERO_NPV_RATE`.

See `examples/xlwings_sheet_template.csv` for a starter table you can paste into Excel.

On macOS, the simplest no-UDF workflow is:

1. Save a workbook as `pyquantlib_workbook.xlsx`.
2. Copy `examples/pyquantlib_workbook.py` into the same folder as the workbook.
3. Paste the contents of `examples/xlwings_sheet_template.csv` into the workbook.
4. Select the sheet with the pricing table.
5. Click the xlwings ribbon button `Run main`.

The `Run main` button calls `main()` in the Python file with the same base name as the workbook. The example `main()` delegates to `pyquantlib_xlwings.runpython.price_active_sheet`.

If Excel converts a pasted date such as `2031-05-22` into `1931-05-22`, the wrapper repairs maturity/expiry dates that are clearly in the previous century. To avoid Excel date guessing altogether, you can type dates directly into cells with formulas such as `=DATE(2031,5,22)`.

If you prefer a normal Excel button, save the workbook as `.xlsm`, import `examples/runpython_macro.bas`, and assign `PricePyqliteActiveSheet` to a button.

If the optional curve/surface columns are blank, the Excel wrapper falls back to flat continuously-compounded curves and a constant volatility. Curve time uses `Actual/365 Fixed`; swap coupons use `Actual/360`.

### Dated Curves And Vol Surfaces

The wrapper also accepts more realistic market data in optional curve/surface columns:

```text
source_curve, target_curve, domestic_curve, foreign_curve, discount_curve, forward_curve, vol_surface
```

Curve cells use semicolon-separated `date:value` nodes. By default values are continuous zero rates:

```text
2027-05-22:0.039;2029-05-22:0.041;2031-05-22:0.043
```

To pass discount factors instead of zero rates, prefix with `discount|`:

```text
discount|2027-05-22:0.962;2029-05-22:0.884;2031-05-22:0.807
```

Volatility curves use the same `date:vol` form:

```text
2027-05-22:0.15;2029-05-22:0.165
```

FX volatility surfaces use market delta columns, followed by expiry rows:

```text
-0.25,ATM,0.25|2027-05-22:0.17,0.15,0.16|2029-05-22:0.19,0.165,0.18
```

The first row is put deltas, optional `ATM`, then call deltas, matching the
QuantLib `BlackVolatilitySurfaceDelta` layout. For a generic strike/expiry
surface, explicitly prefix the cell with `strike|`:

```text
strike|1.10,1.25,1.40|2027-05-22:0.17,0.15,0.16|2029-05-22:0.19,0.165,0.18
```

Internally, `pyquantlib` now includes:

```text
ZeroCurve              linear interpolation on continuous zero rates
DiscountCurve          log-linear interpolation on discount factors
BlackVarianceCurve     interpolation on total variance
BlackDeltaVolSurface   FX delta/expiry surface converted to strike smiles
BlackVarianceSurface   generic strike/expiry surface, available with strike| prefix
ForwardRateAgreement   QuantLib FRA payoff and discounting formula
FixedRateBond          fixed coupons plus redemption discounted from cashflows
CapFloor               Black cap, floor, and collar optionlet pricing
Swaption               physical European swaption priced by Black 76
SwaptionVolatilityMatrix  ATM option-expiry/swap-tenor IR volatility matrix
SwaptionVolatilityCube    ATM matrix plus strike-spread smile layers
SabrSwaptionVolatilityCube SABR parameter surfaces for IR swaption smiles
BermudanSwaption       Bermudan physical swaption with LSM exercise engine
CmsSwap                fixed-vs-CMS swap with swaption-vol convexity adjustment
CrossCurrencyBasisSwap constant-notional float-float XCCY swap
CrossCurrencyFixedFloatSwap constant-notional fixed-float XCCY swap
OvernightIndexedSwap   fixed-vs-compounded-overnight swap
FloatFloatSwap         basis swap with separate schedules, curves, spreads, and gearings
NonstandardSwap        custom per-period notionals/rates/gearings/spreads
DigitalFxOption        cash-or-nothing analytic Garman-Kohlhagen option
FX exotics             path-dependent options through deterministic Monte Carlo engines
Equity exotics         barrier, Asian, lookback, cliquet, forward-start, basket MC engines
```

The path-dependent FX exotic classes are intentionally Python-first because their inputs are richer than a compact spreadsheet row. Use `pyquantlib.McFxExoticEngine` directly from Python for barriers, double barriers/no-touch, Asians, window barriers, forward-start, quanto, lookback, cliquet, and basket/correlation products.

### Swaption Volatility Inputs

`PYQUANTLIB_SWAPTION_NPV` still accepts a plain scalar Black volatility:

```text
0.18
```

For a QuantLib-style ATM swaption volatility matrix, use:

```text
matrix|option tenors|swap tenors|vol rows
matrix|1Y,2Y|5Y,10Y|0.18,0.19;0.20,0.21
```

Rows are option tenors and columns are swap tenors. Interpolation is bilinear in option time and swap length, matching `SwaptionVolatilityMatrix`.

For a strike-spread smile cube, use:

```text
cube|option tenors|swap tenors|ATM vol rows|strike spreads|vol-spread layers
cube|1Y,2Y|5Y,10Y|0.18,0.19;0.20,0.21|-0.01,0,0.01|0.015,0.014;0.013,0.012#0,0;0,0#0.010,0.011;0.012,0.013
```

For a SABR smile cube with supplied parameters:

```text
sabr|option tenors|swap tenors|ATM vol rows|SABR parameter rows
sabr|1Y,2Y|5Y,10Y|0.18,0.19;0.20,0.21|0.03,0.5,0.40,-0.20/0.032,0.5,0.38,-0.18;0.034,0.5,0.36,-0.16/0.036,0.5,0.34,-0.14
```

Each SABR cell is `alpha,beta,nu,rho`. This package converts QuantLib's SABR volatility formula and surface query behavior, but it does not yet include QuantLib's optimizer-based SABR calibration from market smile quotes.
