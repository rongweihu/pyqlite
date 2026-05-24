"""A compact standalone Python pricing kernel for IR and FX products."""

from pyqlite.time.date import Period, TimeUnit
from pyqlite.time.calendar import BusinessDayConvention, Calendar, NullCalendar, WeekendsOnly
from pyqlite.time.daycounter import Actual360, Actual365Fixed, Thirty360, Thirty360Convention
from pyqlite.time.schedule import DateGenerationRule, Schedule
from pyqlite.market.curves import DiscountCurve, FlatForwardCurve, ZeroCurve
from pyqlite.market.default_curves import FlatHazardRate, SurvivalProbabilityCurve
from pyqlite.market.inflation import InflationIndexCurve, ZeroInflationCurve
from pyqlite.market.quote import SimpleQuote
from pyqlite.market.swaption_volatility import (
    ConstantSwaptionVolatility,
    SabrParameters,
    SabrSwaptionVolatilityCube,
    SwaptionVolatilityCube,
    SwaptionVolatilityMatrix,
)
from pyqlite.market.volatility import BlackConstantVol, BlackDeltaVolSurface, BlackVarianceCurve, BlackVarianceSurface
from pyqlite.math.black_delta import AtmType, DeltaType
from pyqlite.indexes.ibor import IborIndex
from pyqlite.instruments.bond import Bond, FixedRateBond, ZeroCouponBond
from pyqlite.instruments.bermudan_swaption import BermudanSwaption
from pyqlite.instruments.capfloor import CapFloor, CapFloorType
from pyqlite.instruments.cms import CmsSwap
from pyqlite.instruments.credit import CdsOption, CreditDefaultSwap, ProtectionSide
from pyqlite.instruments.cross_asset import (
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
from pyqlite.instruments.fra import ForwardRateAgreement, PositionType
from pyqlite.instruments.floatfloat import FloatFloatSwap
from pyqlite.instruments.swap import SwapType, VanillaSwap
from pyqlite.instruments.fx_forward import FxForward
from pyqlite.instruments.fx_exotics import (
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
from pyqlite.instruments.fx_option import FxOption, OptionType
from pyqlite.instruments.equity_exotics import (
    BarrierDirection as EquityBarrierDirection,
    BarrierStyle as EquityBarrierStyle,
    EquityAsianOption,
    EquityBarrierOption,
    EquityBasketOption,
    EquityCliquetOption,
    EquityForwardStartOption,
    EquityLookbackOption,
)
from pyqlite.instruments.nonstandard_swap import NonstandardSwap
from pyqlite.instruments.ois import OvernightIndexedSwap
from pyqlite.instruments.swaption import SettlementType, Swaption
from pyqlite.instruments.xccy import CrossCurrencyBasisSwap, CrossCurrencyFixedFloatSwap
from pyqlite.engines.discounting_swap import DiscountingSwapEngine
from pyqlite.engines.discounting_fx_forward import DiscountingFxForwardEngine
from pyqlite.engines.analytic_fx_option import AnalyticFxOptionEngine
from pyqlite.engines.bermudan_swaption import LsmBermudanSwaptionEngine
from pyqlite.engines.black_capfloor import BlackCapFloorEngine
from pyqlite.engines.black_swaption import BlackSwaptionEngine
from pyqlite.engines.cms_engine import DiscountingCmsSwapEngine
from pyqlite.engines.credit_engines import BlackCdsOptionEngine, CdsResult, MidPointCdsEngine
from pyqlite.engines.cross_asset_engines import (
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
from pyqlite.engines.discounting_bond import DiscountingBondEngine
from pyqlite.engines.discounting_fra import DiscountingFraEngine
from pyqlite.engines.equity_exotic_engines import McEquityExoticEngine
from pyqlite.engines.fx_exotic_engines import AnalyticDigitalFxOptionEngine, FxExoticResult, McFxExoticEngine
from pyqlite.engines.xccy_engine import DiscountingCrossCurrencySwapEngine, XccyBasisSwapResult, XccyFixedFloatSwapResult

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
