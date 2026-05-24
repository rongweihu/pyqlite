"""A compact standalone Python pricing kernel for IR and FX products."""

from pyquantlib.time.date import Period, TimeUnit
from pyquantlib.time.calendar import BusinessDayConvention, Calendar, NullCalendar, WeekendsOnly
from pyquantlib.time.daycounter import Actual360, Actual365Fixed, Thirty360, Thirty360Convention
from pyquantlib.time.schedule import DateGenerationRule, Schedule
from pyquantlib.market.curves import DiscountCurve, FlatForwardCurve, ZeroCurve
from pyquantlib.market.default_curves import FlatHazardRate, SurvivalProbabilityCurve
from pyquantlib.market.inflation import InflationIndexCurve, ZeroInflationCurve
from pyquantlib.market.quote import SimpleQuote
from pyquantlib.market.swaption_volatility import (
    ConstantSwaptionVolatility,
    SabrParameters,
    SabrSwaptionVolatilityCube,
    SwaptionVolatilityCube,
    SwaptionVolatilityMatrix,
)
from pyquantlib.market.volatility import BlackConstantVol, BlackDeltaVolSurface, BlackVarianceCurve, BlackVarianceSurface
from pyquantlib.math.black_delta import AtmType, DeltaType
from pyquantlib.indexes.ibor import IborIndex
from pyquantlib.instruments.bond import Bond, FixedRateBond, ZeroCouponBond
from pyquantlib.instruments.bermudan_swaption import BermudanSwaption
from pyquantlib.instruments.capfloor import CapFloor, CapFloorType
from pyquantlib.instruments.cms import CmsSwap
from pyquantlib.instruments.credit import CdsOption, CreditDefaultSwap, ProtectionSide
from pyquantlib.instruments.cross_asset import (
    CommodityForward,
    CommodityOption,
    CommoditySwap,
    EquityOption,
    EquityTotalReturnSwap,
    VarianceSwap,
    VolatilitySwap,
    YearOnYearInflationSwap,
    ZeroCouponInflationSwap,
)
from pyquantlib.instruments.fra import ForwardRateAgreement, PositionType
from pyquantlib.instruments.floatfloat import FloatFloatSwap
from pyquantlib.instruments.swap import SwapType, VanillaSwap
from pyquantlib.instruments.fx_forward import FxForward
from pyquantlib.instruments.fx_exotics import (
    AsianFxOption,
    BarrierDirection,
    BarrierFxOption,
    BarrierStyle,
    BasketFxOption,
    CliquetFxOption,
    DigitalFxOption,
    DoubleBarrierFxOption,
    ForwardStartFxOption,
    LookbackFxOption,
    QuantoFxOption,
    WindowBarrierFxOption,
)
from pyquantlib.instruments.fx_option import FxOption, OptionType
from pyquantlib.instruments.equity_exotics import (
    BarrierDirection as EquityBarrierDirection,
    BarrierStyle as EquityBarrierStyle,
    EquityAsianOption,
    EquityBarrierOption,
    EquityBasketOption,
    EquityCliquetOption,
    EquityForwardStartOption,
    EquityLookbackOption,
)
from pyquantlib.instruments.nonstandard_swap import NonstandardSwap
from pyquantlib.instruments.ois import OvernightIndexedSwap
from pyquantlib.instruments.swaption import SettlementType, Swaption
from pyquantlib.instruments.xccy import CrossCurrencyBasisSwap, CrossCurrencyFixedFloatSwap
from pyquantlib.engines.discounting_swap import DiscountingSwapEngine
from pyquantlib.engines.discounting_fx_forward import DiscountingFxForwardEngine
from pyquantlib.engines.analytic_fx_option import AnalyticFxOptionEngine
from pyquantlib.engines.bermudan_swaption import LsmBermudanSwaptionEngine
from pyquantlib.engines.black_capfloor import BlackCapFloorEngine
from pyquantlib.engines.black_swaption import BlackSwaptionEngine
from pyquantlib.engines.cms_engine import DiscountingCmsSwapEngine
from pyquantlib.engines.credit_engines import BlackCdsOptionEngine, CdsResult, MidPointCdsEngine
from pyquantlib.engines.cross_asset_engines import (
    AnalyticCommodityOptionEngine,
    AnalyticEquityOptionEngine,
    DiscountingCommodityForwardEngine,
    DiscountingCommoditySwapEngine,
    DiscountingEquityTotalReturnSwapEngine,
    DiscountingInflationSwapEngine,
    PricingResult,
    VarianceSwapEngine,
    VolatilitySwapEngine,
)
from pyquantlib.engines.discounting_bond import DiscountingBondEngine
from pyquantlib.engines.discounting_fra import DiscountingFraEngine
from pyquantlib.engines.equity_exotic_engines import McEquityExoticEngine
from pyquantlib.engines.fx_exotic_engines import AnalyticDigitalFxOptionEngine, FxExoticResult, McFxExoticEngine
from pyquantlib.engines.xccy_engine import DiscountingCrossCurrencySwapEngine, XccyBasisSwapResult, XccyFixedFloatSwapResult

__all__ = [
    "Actual360",
    "Actual365Fixed",
    "AnalyticFxOptionEngine",
    "AnalyticDigitalFxOptionEngine",
    "AnalyticCommodityOptionEngine",
    "AnalyticEquityOptionEngine",
    "AsianFxOption",
    "AtmType",
    "BarrierDirection",
    "BarrierFxOption",
    "BarrierStyle",
    "BasketFxOption",
    "BermudanSwaption",
    "BlackCapFloorEngine",
    "BlackCdsOptionEngine",
    "BlackConstantVol",
    "BlackDeltaVolSurface",
    "BlackSwaptionEngine",
    "BlackVarianceCurve",
    "BlackVarianceSurface",
    "Bond",
    "BusinessDayConvention",
    "Calendar",
    "CapFloor",
    "CapFloorType",
    "CdsOption",
    "CdsResult",
    "CliquetFxOption",
    "CmsSwap",
    "CommodityForward",
    "CommodityOption",
    "CommoditySwap",
    "ConstantSwaptionVolatility",
    "CreditDefaultSwap",
    "CrossCurrencyBasisSwap",
    "CrossCurrencyFixedFloatSwap",
    "DateGenerationRule",
    "DiscountCurve",
    "DiscountingBondEngine",
    "DiscountingCmsSwapEngine",
    "DiscountingCrossCurrencySwapEngine",
    "DiscountingCommodityForwardEngine",
    "DiscountingCommoditySwapEngine",
    "DiscountingEquityTotalReturnSwapEngine",
    "DiscountingFraEngine",
    "DiscountingFxForwardEngine",
    "DiscountingInflationSwapEngine",
    "DiscountingSwapEngine",
    "DeltaType",
    "DigitalFxOption",
    "DoubleBarrierFxOption",
    "FixedRateBond",
    "FloatFloatSwap",
    "FlatHazardRate",
    "FlatForwardCurve",
    "ForwardRateAgreement",
    "ForwardStartFxOption",
    "EquityOption",
    "EquityAsianOption",
    "EquityBarrierDirection",
    "EquityBarrierOption",
    "EquityBarrierStyle",
    "EquityBasketOption",
    "EquityCliquetOption",
    "EquityForwardStartOption",
    "EquityLookbackOption",
    "EquityTotalReturnSwap",
    "FxForward",
    "FxExoticResult",
    "FxOption",
    "IborIndex",
    "InflationIndexCurve",
    "LookbackFxOption",
    "LsmBermudanSwaptionEngine",
    "McEquityExoticEngine",
    "McFxExoticEngine",
    "MidPointCdsEngine",
    "NonstandardSwap",
    "NullCalendar",
    "OptionType",
    "OvernightIndexedSwap",
    "Period",
    "PositionType",
    "PricingResult",
    "ProtectionSide",
    "QuantoFxOption",
    "Schedule",
    "SabrParameters",
    "SabrSwaptionVolatilityCube",
    "SettlementType",
    "SimpleQuote",
    "SwapType",
    "Swaption",
    "SwaptionVolatilityCube",
    "SwaptionVolatilityMatrix",
    "SurvivalProbabilityCurve",
    "Thirty360",
    "Thirty360Convention",
    "TimeUnit",
    "VanillaSwap",
    "VarianceSwap",
    "VarianceSwapEngine",
    "VolatilitySwap",
    "VolatilitySwapEngine",
    "XccyBasisSwapResult",
    "XccyFixedFloatSwapResult",
    "WeekendsOnly",
    "WindowBarrierFxOption",
    "YearOnYearInflationSwap",
    "ZeroCurve",
    "ZeroCouponBond",
    "ZeroCouponInflationSwap",
    "ZeroInflationCurve",
]
