# QuantLib Conversion Audit

This package is a standalone Python subset for IR and FX front-office pricing. It is not a wrapper around QuantLib, but the implementation is intentionally mapped to the relevant QuantLib architecture.

## QuantLib Product Inventory

The local QuantLib source tree includes instruments and engines for fixed/floating swaps, zero-coupon swaps, OIS, float-float swaps, multiple-reset swaps, cross-currency swaps, FRAs, caps/floors/collars, swaptions, fixed/floating/zero/amortizing/convertible bonds, bond forwards, asset swaps, CDS, inflation swaps and caps/floors, futures, variance swaps, stocks, vanilla equity options, barrier/double-barrier/partial-time/soft-barrier options, Asian options, basket/spread options, lookback options, chooser/compound/extensible options, Margrabe/two-asset products, quanto products, cliquets, and swing/storage options.

`pyquantlib` intentionally converts the products that fit the current standalone IR/FX architecture and standard-library-only engine set. Products requiring full bootstrapping, credit curves, inflation indexes, equity-dividend models, finite-difference/lattice/Monte-Carlo frameworks, or full observer/handle relinking remain outside the current package scope.

## Converted Components

| Python component | QuantLib source analogue | Notes |
| --- | --- | --- |
| `pyquantlib.time.calendar` | `ql/time/calendar.*` | Business-day adjustment and `Calendar::advance` behavior for days, weeks, months/years, and business end-of-month. Current package implements `NullCalendar` and `WeekendsOnly`; full country calendars are not converted. |
| `pyquantlib.time.schedule` | `ql/time/schedule.*` | Forward/backward schedule generation with business-day adjustment. Irregular stubs and the full QuantLib date-generation matrix are not converted. |
| `pyquantlib.time.daycounter` | `ql/time/daycounters/*` | `Actual360`, `Actual365Fixed`, and `Thirty360` conventions: USA, BondBasis/ISMA, European/EurobondBasis, Italian, ISDA/German, NASD. |
| `pyquantlib.market.curves.DiscountCurve` | `ql/termstructures/yield/discountcurve.hpp` | Log-linear interpolation of discount factors with flat-forward long-end extrapolation. Python constructor uses the explicit `reference_date` plus future pillars, equivalent to QuantLib's implicit reference discount of 1.0. |
| `pyquantlib.market.curves.ZeroCurve` | `ql/termstructures/yield/zerocurve.hpp` | Linear interpolation of continuous zero rates, with long-end extrapolation by terminal instantaneous-forward behavior. |
| `pyquantlib.market.volatility.BlackVarianceCurve` | `ql/termstructures/volatility/equityfx/blackvariancecurve.*` | Interpolates total variance over expiry and flat-vol extrapolates in time. Monotone variance is enforced by default, as in QuantLib; the delta surface disables it for per-delta columns, as QuantLib does. |
| `pyquantlib.market.volatility.BlackVarianceSurface` | `ql/termstructures/volatility/equityfx/blackvariancesurface.*` | Generic strike/expiry surface, interpolating total variance. This is not the FX market delta surface. Strike extrapolation follows the interpolator by default. |
| `pyquantlib.math.black_delta.BlackDeltaCalculator` | `ql/pricingengines/blackdeltacalculator.*` | Supports spot, forward, premium-adjusted spot, and premium-adjusted forward delta conventions, plus key ATM conventions. |
| `pyquantlib.market.volatility.BlackDeltaVolSurface` | `ql/termstructures/volatility/equityfx/blackvolsurfacedelta.*` | FX delta/expiry vol surface. Converts put/ATM/call delta pillars to strike smiles through `BlackDeltaCalculator`, uses term-structure-time discounting, and interpolates volatility by strike. |
| `pyquantlib.math.black.black_formula` | `ql/pricingengines/blackformula.*` and `BlackCalculator` use pattern | European Black formula and core sensitivities used by FX option engine. |
| `pyquantlib.engines.analytic_fx_option` | `ql/pricingengines/vanilla/analyticeuropeanengine.cpp` with `GarmanKohlagenProcess` | Uses domestic/foreign discount curves, Black variance, and Black formula. |
| `pyquantlib.instruments.fx_forward` and `engines.discounting_fx_forward` | `ql/instruments/fxforward.*`, `ql/pricingengines/forward/discountingfxforwardengine.*` | Discounts source/target legs and reports QuantLib's `fairForwardRate`. Python also exposes `zero_npv_forward_rate` for spreadsheet users who want the contract rate that reprices the wrapper trade to zero. |
| `pyquantlib.instruments.swap` and `engines.discounting_swap` | `ql/instruments/swap.*`, `vanillaswap.*`, `discountingswapengine.*` | Builds fixed/floating legs and discounts cashflows. |
| `pyquantlib.instruments.ois` | `ql/instruments/overnightindexedswap.*` | Fixed leg versus compounded overnight leg. The overnight coupon compounds through the forwarding curve discount ratio, then applies the spread. Telescopic value-date optimization and averaging-rate variants are outside this compact conversion. |
| `pyquantlib.instruments.floatfloat` | `ql/instruments/floatfloatswap.*` | Two floating legs with independent schedules, indexes, notionals, gearings, spreads, and optional intermediate/final capital exchanges. |
| `pyquantlib.instruments.nonstandard_swap` | `ql/instruments/nonstandardswap.*` | Custom fixed/floating notionals, fixed rates, floating gearings, spreads, schedules, and capital exchanges. |
| `pyquantlib.instruments.fra` and `engines.discounting_fra` | `ql/instruments/forwardrateagreement.*` | Uses QuantLib's FRA payoff formula `N * sign * (F-K) * tau / (1+F*tau)` and discounts the settlement amount to value date. |
| `pyquantlib.instruments.bond` and `engines.discounting_bond` | `ql/instruments/bond.*`, `bonds/fixedratebond.*`, `bonds/zerocouponbond.*`, `pricingengines/bond/discountingbondengine.*` | Fixed coupons plus redemption are represented as cashflows and discounted with settlement-value handling. |
| `pyquantlib.instruments.capfloor` and `engines.black_capfloor` | `ql/instruments/capfloor.*`, `pricingengines/capfloor/blackcapfloorengine.*` | Builds cap/floor/collar optionlets from an Ibor leg and values them with shifted-lognormal Black formula. |
| `pyquantlib.instruments.swaption` and `engines.black_swaption` | `ql/instruments/swaption.*`, `pricingengines/swaption/blackswaptionengine.*` | Supports physical European swaptions on vanilla swaps using Black 76, fixed-leg annuity, fair swap rate, spread correction, and Black vega/delta outputs. |
| `pyquantlib.instruments.bermudan_swaption.BermudanSwaption` and `LsmBermudanSwaptionEngine` | `ql/instruments/swaption.*`, `pricingengines/swaption/treeswaptionengine.*`, market-model LSM swaption products | Bermudan exercise dates on a physical swaption with early-exercise valuation via Longstaff-Schwartz regression on simulated swap-rate paths. This is a compact standalone alternative to QuantLib's short-rate lattice and market-model engines. |
| `pyquantlib.instruments.cms.CmsSwap` and `DiscountingCmsSwapEngine` | `ql/cashflows/cmscoupon.*`, `makecms.*`, CMS coupon pricers | Fixed-vs-CMS swap where CMS coupons use forward swap rates and optional swaption-vol convexity adjustment. Full Hagan replication/pricer settings are not included. |
| `pyquantlib.instruments.xccy` and `DiscountingCrossCurrencySwapEngine` | `ql/instruments/constnotionalcrosscurrencyswap.*`, `constnotionalcrosscurrencybasisswap.*`, `constnotionalcrosscurrencyfixedvsfloatingswap.*`, `pricingengines/swap/discountingconstnotionalcrosscurrencyswapengine.*` | Constant-notional XCCY basis and fixed-vs-floating swaps. Each leg is discounted in its currency and foreign leg values are converted to domestic currency with spot FX. |
| `pyquantlib.market.swaption_volatility.ConstantSwaptionVolatility` | `ql/termstructures/volatility/swaption/swaptionconstantvol.*` | Constant Black swaption volatility with optional displacement/shift. Existing `BlackConstantVol` remains accepted for backward compatibility. |
| `pyquantlib.market.swaption_volatility.SwaptionVolatilityMatrix` | `ql/termstructures/volatility/swaption/swaptionvolmatrix.*` | ATM option-expiry/swap-tenor matrix with bilinear interpolation in option time and swap length. |
| `pyquantlib.market.swaption_volatility.SwaptionVolatilityCube` | `ql/termstructures/volatility/swaption/swaptionvolcube.*`, `interpolatedswaptionvolatilitycube.*` | ATM matrix plus strike-spread vol-spread layers. Local smile vol is ATM vol plus interpolated vol spread, with linear strike-spread interpolation. |
| `pyquantlib.market.swaption_volatility.SabrSwaptionVolatilityCube` | `ql/termstructures/volatility/swaption/sabrswaptionvolatilitycube.hpp`, `ql/termstructures/volatility/sabr.*` | Fit-early/interpolate-later SABR cube behavior using supplied alpha/beta/nu/rho parameter surfaces and QuantLib's shifted lognormal SABR formula. Optimizer calibration from market smiles is intentionally not included yet. |
| `pyquantlib.instruments.fx_exotics.DigitalFxOption` and `AnalyticDigitalFxOptionEngine` | `ql/instruments/vanillaoption.*`, `ql/instruments/payoffs.*`, `analyticeuropeanengine.*` | Cash-or-nothing digital payoff under the same domestic/foreign Garman-Kohlhagen setup as the vanilla FX option. |
| `pyquantlib.instruments.fx_exotics.BarrierFxOption` | `ql/instruments/barrieroption.*` and barrier engines | Single up/down, in/out barrier product representation. Pricing is provided by the compact deterministic Monte Carlo engine rather than QuantLib's full analytic/FD/barrier-engine family. |
| `pyquantlib.instruments.fx_exotics.DoubleBarrierFxOption` | `ql/instruments/doublebarrieroption.*` | Double knock-in/knock-out and double-no-touch style payoff representation, priced by deterministic Monte Carlo. |
| `pyquantlib.instruments.fx_exotics.AsianFxOption` | `ql/instruments/asianoption.*` | Average-rate arithmetic Asian payoff, priced by deterministic Monte Carlo. |
| `pyquantlib.instruments.fx_exotics.WindowBarrierFxOption` | `ql/instruments/partialtimebarrieroption.*` | Barrier monitoring restricted to a start/end window, priced by deterministic Monte Carlo. |
| `pyquantlib.instruments.fx_exotics.ForwardStartFxOption` | `ql/instruments/forwardvanillaoption.*` | Forward-start strike set from the future spot times a moneyness factor, then priced along paths. |
| `pyquantlib.instruments.fx_exotics.QuantoFxOption` | QuantLib quanto option engine pattern | Domestic drift adjustment includes equity/FX correlation and vol terms in the standard quanto style. |
| `pyquantlib.instruments.fx_exotics.LookbackFxOption` | `ql/instruments/lookbackoption.*` | Floating/fixed lookback-style extrema payoffs under deterministic Monte Carlo. |
| `pyquantlib.instruments.fx_exotics.CliquetFxOption` | `ql/instruments/cliquetoption.*` | Periodic capped/floored return accumulation. |
| `pyquantlib.instruments.fx_exotics.BasketFxOption` | `ql/instruments/basketoption.*` and spread/basket engines | Multi-FX correlated lognormal paths with Cholesky correlation and basket payoff. |
| `pyquantlib.market.default_curves` | `ql/termstructures/defaulttermstructure.*` | Flat hazard-rate and interpolated survival-probability curves for CDS pricing. |
| `pyquantlib.instruments.credit.CreditDefaultSwap` and `MidPointCdsEngine` | `ql/instruments/creditdefaultswap.*`, `pricingengines/credit/midpointcdsengine.*` | Running-spread CDS with protection buyer/seller signs, premium leg, accrual-on-default, default leg, fair spread, and coupon BPS. ISDA date-grid details are outside this compact conversion. |
| `pyquantlib.instruments.credit.CdsOption` and `BlackCdsOptionEngine` | `ql/experimental/credit/cdsoption.*`, `blackcdsoptionengine.*` | European option on CDS spread using Black formula over the risky annuity. |
| `pyquantlib.instruments.equity.EquityOption` and `AnalyticEquityOptionEngine` | `ql/instruments/vanillaoption.*`, `stock.*`, Black-Scholes-Merton process | European equity option with spot, dividend curve, risk-free curve, and Black volatility. |
| `pyquantlib.instruments.equity.EquityTotalReturnSwap` and `DiscountingEquityTotalReturnSwapEngine` | `ql/instruments/equitytotalreturnswap.*`, `cashflows/equitycashflow.*` | Equity forward total-return leg versus floating funding leg, with QuantLib-style payer signs and fair margin formula. |
| `pyquantlib.instruments.equity_exotics` and `McEquityExoticEngine` | `ql/instruments/barrieroption.*`, `asianoption.*`, `lookbackoption.*`, `cliquetoption.*`, `basketoption.*`, `forwardvanillaoption.*` plus respective analytic/MC/FD engines | Equity barrier, Asian, lookback, cliquet, forward-start, and basket products under a Black-Scholes-Merton-style Monte Carlo engine. |
| `pyquantlib.instruments.commodity.CommodityForward`, `CommoditySwap`, `CommodityOption` | `ql/experimental/commodities/*`, `pricingengines/forward/*` | Commodity forwards/swaps/options using supplied commodity forward/carry curve and Black option pricing. |
| `pyquantlib.market.inflation` and inflation swaps | `ql/termstructures/inflation/*`, `zerocouponinflationswap.*`, `yearonyearinflationswap.*` | Zero-coupon and year-on-year inflation swaps from supplied zero/index inflation curve and nominal discount curve. |
| `pyquantlib.instruments.variance.VarianceSwap` and `VarianceSwapEngine` | `ql/instruments/varianceswap.*`, `pricingengines/forward/replicatingvarianceswapengine.*` | Variance swap payoff over forward fair variance between start and maturity from a Black variance term structure. Full static replication from option strips is not included. |
| `pyquantlib.instruments.variance.VolatilitySwap` and `VolatilitySwapEngine` | QuantLib variance-volatility product pattern | Volatility swap payoff over fair forward Black volatility. |

## Intentional Scope Limits

- No curve bootstrapping from deposits, FRAs, futures, OIS, or swaps yet; FRAs are priced from already-built curves.
- No full QuantLib observer/handle/lazy-object graph.
- No full holiday calendar library.
- No stochastic local-vol, Heston, finite-difference, tree, or full QuantLib Monte Carlo framework. The package has compact deterministic Monte Carlo engines for the requested FX and equity path-dependent products, plus an LSM Bermudan swaption engine.
- No optimizer-based swaption SABR calibration yet; `SabrSwaptionVolatilityCube` expects supplied parameter surfaces.
- No full interpolator family; current package implements the practical linear/log-linear/variance interpolation subset.
- No full QuantLib `SmileSection` abstraction; `BlackDeltaVolSurface` performs the delta-to-strike conversion and direct strike interpolation needed by the FX option pricer.
- No long-term delta/ATM convention switch, cubic smile interpolation, or observer/handle relinking in the FX delta surface.
- No cash-settled swaption annuity models, calibrated lattice short-rate models, or normal/Bachelier cap/swaption engines yet.
- Full CMS Hagan replication pricers, XCCY collateral/FX-settlement-date basis adjustments, amortizing/floating/convertible bond families, asset swaps, detailed commodity storage/swing products, and ISDA-standard CDS engine mechanics are not converted yet.

## FX Vol Surface Convention

For FX options, the Excel `vol_surface` input now follows QuantLib's delta surface layout:

```text
put deltas, ATM, call deltas | expiry: vols | expiry: vols
```

Example:

```text
-0.25,ATM,0.25|2027-05-22:0.17,0.15,0.16|2029-05-22:0.19,0.165,0.18
```

Generic strike/expiry surfaces remain available, but must be explicitly prefixed:

```text
strike|1.10,1.25,1.40|2027-05-22:0.17,0.15,0.16|2029-05-22:0.19,0.165,0.18
```
