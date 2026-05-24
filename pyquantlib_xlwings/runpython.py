from __future__ import annotations

try:
    import xlwings as xw
except ImportError as exc:
    raise RuntimeError("pyquantlib_xlwings.runpython requires xlwings to be installed") from exc

from pyquantlib_xlwings.functions import (
    PYQUANTLIB_BERMUDAN_SWAPTION_NPV,
    PYQUANTLIB_CAPFLOOR_NPV,
    PYQUANTLIB_CDS_NPV,
    PYQUANTLIB_CDS_OPTION_NPV,
    PYQUANTLIB_CMS_SWAP_FAIR_RATE,
    PYQUANTLIB_CMS_SWAP_NPV,
    PYQUANTLIB_COMMODITY_FORWARD_NPV,
    PYQUANTLIB_COMMODITY_OPTION_NPV,
    PYQUANTLIB_COMMODITY_SWAP_NPV,
    PYQUANTLIB_DIGITAL_FX_OPTION_NPV,
    PYQUANTLIB_EQUITY_ASIAN_OPTION_NPV,
    PYQUANTLIB_EQUITY_BARRIER_OPTION_NPV,
    PYQUANTLIB_EQUITY_OPTION_NPV,
    PYQUANTLIB_EQUITY_TRS_NPV,
    PYQUANTLIB_FIXED_BOND_NPV,
    PYQUANTLIB_FLOAT_FLOAT_NPV,
    PYQUANTLIB_FRA_NPV,
    PYQUANTLIB_FX_FORWARD_NPV,
    PYQUANTLIB_FX_FORWARD_RATE,
    PYQUANTLIB_FX_FORWARD_ZERO_NPV_RATE,
    PYQUANTLIB_FX_OPTION_NPV,
    PYQUANTLIB_NONSTANDARD_SWAP_NPV,
    PYQUANTLIB_OIS_FAIR_RATE,
    PYQUANTLIB_OIS_NPV,
    PYQUANTLIB_SWAPTION_NPV,
    PYQUANTLIB_SWAP_FAIR_RATE,
    PYQUANTLIB_SWAP_NPV,
    PYQUANTLIB_VARIANCE_SWAP_NPV,
    PYQUANTLIB_VOLATILITY_SWAP_NPV,
    PYQUANTLIB_XCCY_BASIS_SWAP_FAIR_PAY_SPREAD,
    PYQUANTLIB_XCCY_BASIS_SWAP_NPV,
    PYQUANTLIB_XCCY_FIXED_FLOAT_NPV,
    PYQUANTLIB_YOY_INFLATION_SWAP_NPV,
    PYQUANTLIB_ZC_INFLATION_SWAP_NPV,
)


def price_active_sheet() -> None:
    """Price rows on the active Excel sheet.

    Expected columns on row 1:
    product, output, evaluation_date, maturity_date, spot_fx, source_nominal,
    contract_forward_rate, source_rate, target_rate, option_type, strike,
    foreign_notional, domestic_rate, foreign_rate, volatility, nominal,
    fixed_rate, discount_rate, forward_rate, pay_fixed.

    Results are written to the output column for rows 2 onward.
    """
    book = xw.Book.caller()
    sheet = book.sheets.active
    headers = [str(value).strip() if value is not None else "" for value in sheet.range("1:1").value]
    columns = {header: index + 1 for index, header in enumerate(headers) if header}
    output_col = columns.get("output")
    product_col = columns.get("product")
    if not output_col or not product_col:
        raise ValueError("sheet must include 'product' and 'output' headers")

    row = 2
    while True:
        product = sheet.cells(row, product_col).value
        if product in (None, ""):
            break
        try:
            sheet.cells(row, output_col).value = _price_row(sheet, columns, row, str(product).strip().upper())
        except Exception as exc:
            sheet.cells(row, output_col).value = f"ERROR row {row}: {exc}; inputs={_row_inputs(sheet, columns, row)}"
        row += 1


def _price_row(sheet, columns: dict[str, int], row: int, product: str) -> float:
    def get(name, default=None):
        if name not in columns:
            return default
        value = sheet.cells(row, columns[name]).value
        return default if value in (None, "") else value

    if product == "FX_FORWARD_RATE":
        return PYQUANTLIB_FX_FORWARD_RATE(
            get("evaluation_date"),
            get("maturity_date"),
            get("spot_fx"),
            get("source_rate"),
            get("target_rate"),
            get("settlement_days", 2),
            get("source_curve"),
            get("target_curve"),
        )
    if product == "FX_FORWARD_ZERO_NPV_RATE":
        return PYQUANTLIB_FX_FORWARD_ZERO_NPV_RATE(
            get("evaluation_date"),
            get("maturity_date"),
            get("spot_fx"),
            get("source_rate"),
            get("target_rate"),
            get("settlement_days", 2),
            get("source_curve"),
            get("target_curve"),
        )
    if product == "FX_FORWARD_NPV":
        return PYQUANTLIB_FX_FORWARD_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("spot_fx"),
            get("source_nominal"),
            get("contract_forward_rate"),
            get("source_rate"),
            get("target_rate"),
            get("pay_source_currency", True),
            get("settlement_days", 2),
            get("source_curve"),
            get("target_curve"),
        )
    if product == "FX_OPTION_NPV":
        return PYQUANTLIB_FX_OPTION_NPV(
            get("option_type"),
            get("evaluation_date"),
            get("maturity_date"),
            get("spot_fx"),
            get("strike"),
            get("foreign_notional"),
            get("domestic_rate"),
            get("foreign_rate"),
            get("volatility"),
            get("domestic_curve"),
            get("foreign_curve"),
            get("vol_surface"),
        )
    if product == "DIGITAL_FX_OPTION_NPV":
        return PYQUANTLIB_DIGITAL_FX_OPTION_NPV(
            get("option_type"),
            get("evaluation_date"),
            get("maturity_date"),
            get("spot_fx"),
            get("strike"),
            get("notional"),
            get("cash_payoff"),
            get("domestic_rate"),
            get("foreign_rate"),
            get("volatility"),
            get("domestic_curve"),
            get("foreign_curve"),
        )
    if product == "FRA_NPV":
        return PYQUANTLIB_FRA_NPV(
            get("evaluation_date"),
            get("value_date"),
            get("maturity_date"),
            get("notional"),
            get("strike_rate"),
            get("forward_rate"),
            get("discount_rate"),
            get("long_position", True),
            get("settlement_days", 2),
            get("forward_curve"),
            get("discount_curve"),
        )
    if product == "FIXED_BOND_NPV":
        return PYQUANTLIB_FIXED_BOND_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("face_amount"),
            get("coupon_rate"),
            get("discount_rate"),
            get("frequency_months", 12),
            get("settlement_days", 2),
            get("discount_curve"),
        )
    if product == "CAPFLOOR_NPV":
        return PYQUANTLIB_CAPFLOOR_NPV(
            get("cap_floor_type"),
            get("evaluation_date"),
            get("start_date"),
            get("maturity_date"),
            get("notional"),
            get("cap_rate"),
            get("floor_rate"),
            get("forward_rate"),
            get("discount_rate"),
            get("volatility"),
            get("frequency_months", 6),
            get("floating_spread", 0.0),
            get("forward_curve"),
            get("discount_curve"),
        )
    if product == "SWAPTION_NPV":
        return PYQUANTLIB_SWAPTION_NPV(
            get("evaluation_date"),
            get("exercise_date"),
            get("maturity_date"),
            get("nominal"),
            get("fixed_rate"),
            get("discount_rate"),
            get("forward_rate"),
            get("volatility"),
            get("pay_fixed", True),
            get("fixed_frequency_months", 6),
            get("floating_frequency_months", 6),
            get("floating_spread", 0.0),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "SWAP_FAIR_RATE":
        return PYQUANTLIB_SWAP_FAIR_RATE(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal"),
            get("discount_rate"),
            get("forward_rate"),
            get("pay_fixed", True),
            get("fixed_frequency_months", 6),
            get("floating_frequency_months", 6),
            get("floating_spread", 0.0),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "SWAP_NPV":
        return PYQUANTLIB_SWAP_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal"),
            get("fixed_rate"),
            get("discount_rate"),
            get("forward_rate"),
            get("pay_fixed", True),
            get("fixed_frequency_months", 6),
            get("floating_frequency_months", 6),
            get("floating_spread", 0.0),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "OIS_NPV":
        return PYQUANTLIB_OIS_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal"),
            get("fixed_rate"),
            get("discount_rate"),
            get("overnight_rate"),
            get("pay_fixed", True),
            get("frequency_months", 12),
            get("floating_spread", 0.0),
            get("discount_curve"),
            get("overnight_curve"),
        )
    if product == "OIS_FAIR_RATE":
        return PYQUANTLIB_OIS_FAIR_RATE(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal"),
            get("discount_rate"),
            get("overnight_rate"),
            get("pay_fixed", True),
            get("frequency_months", 12),
            get("floating_spread", 0.0),
            get("discount_curve"),
            get("overnight_curve"),
        )
    if product == "FLOAT_FLOAT_NPV":
        return PYQUANTLIB_FLOAT_FLOAT_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal1"),
            get("nominal2"),
            get("discount_rate"),
            get("forward_rate1"),
            get("forward_rate2"),
            get("spread1", 0.0),
            get("spread2", 0.0),
            get("pay_leg1", True),
            get("frequency1_months", 3),
            get("frequency2_months", 6),
            get("discount_curve"),
            get("forward_curve1"),
            get("forward_curve2"),
        )
    if product == "NONSTANDARD_SWAP_NPV":
        return PYQUANTLIB_NONSTANDARD_SWAP_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("fixed_nominals"),
            get("floating_nominals"),
            get("fixed_rates"),
            get("discount_rate"),
            get("forward_rate"),
            get("pay_fixed", True),
            get("frequency_months", 6),
            get("gearings"),
            get("spreads"),
            get("intermediate_capital_exchange", False),
            get("final_capital_exchange", False),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "BERMUDAN_SWAPTION_NPV":
        return PYQUANTLIB_BERMUDAN_SWAPTION_NPV(
            get("evaluation_date"),
            get("exercise_dates"),
            get("maturity_date"),
            get("nominal"),
            get("fixed_rate"),
            get("discount_rate"),
            get("forward_rate"),
            get("volatility"),
            get("pay_fixed", True),
            get("fixed_frequency_months", 6),
            get("floating_frequency_months", 6),
            get("floating_spread", 0.0),
            get("paths", 1024),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "CMS_SWAP_NPV":
        return PYQUANTLIB_CMS_SWAP_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal"),
            get("fixed_rate"),
            get("discount_rate"),
            get("forward_rate"),
            get("cms_tenor_months", 60),
            get("pay_fixed", True),
            get("frequency_months", 12),
            get("spread", 0.0),
            get("gearing", 1.0),
            get("volatility"),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "CMS_SWAP_FAIR_RATE":
        return PYQUANTLIB_CMS_SWAP_FAIR_RATE(
            get("evaluation_date"),
            get("maturity_date"),
            get("nominal"),
            get("discount_rate"),
            get("forward_rate"),
            get("cms_tenor_months", 60),
            get("pay_fixed", True),
            get("frequency_months", 12),
            get("spread", 0.0),
            get("gearing", 1.0),
            get("volatility"),
            get("discount_curve"),
            get("forward_curve"),
        )
    if product == "XCCY_BASIS_SWAP_NPV":
        return PYQUANTLIB_XCCY_BASIS_SWAP_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("pay_nominal"),
            get("receive_nominal"),
            get("spot_fx"),
            get("domestic_rate"),
            get("foreign_rate"),
            get("pay_spread", 0.0),
            get("receive_spread", 0.0),
            get("pay_leg_domestic", True),
            get("frequency_months", 6),
            get("domestic_curve"),
            get("foreign_curve"),
        )
    if product == "XCCY_BASIS_SWAP_FAIR_PAY_SPREAD":
        return PYQUANTLIB_XCCY_BASIS_SWAP_FAIR_PAY_SPREAD(
            get("evaluation_date"),
            get("maturity_date"),
            get("pay_nominal"),
            get("receive_nominal"),
            get("spot_fx"),
            get("domestic_rate"),
            get("foreign_rate"),
            get("pay_spread", 0.0),
            get("receive_spread", 0.0),
            get("pay_leg_domestic", True),
            get("frequency_months", 6),
            get("domestic_curve"),
            get("foreign_curve"),
        )
    if product == "XCCY_FIXED_FLOAT_NPV":
        return PYQUANTLIB_XCCY_FIXED_FLOAT_NPV(
            get("evaluation_date"),
            get("maturity_date"),
            get("fixed_nominal"),
            get("float_nominal"),
            get("spot_fx"),
            get("fixed_rate"),
            get("domestic_rate"),
            get("foreign_rate"),
            get("float_spread", 0.0),
            get("pay_fixed", True),
            get("fixed_leg_domestic", True),
            get("frequency_months", 6),
            get("domestic_curve"),
            get("foreign_curve"),
        )
    if product == "EQUITY_OPTION_NPV":
        return PYQUANTLIB_EQUITY_OPTION_NPV(get("option_type"), get("evaluation_date"), get("maturity_date"), get("spot"), get("strike"), get("quantity"), get("risk_free_rate"), get("dividend_rate"), get("volatility"))
    if product == "EQUITY_BARRIER_OPTION_NPV":
        return PYQUANTLIB_EQUITY_BARRIER_OPTION_NPV(get("option_type"), get("evaluation_date"), get("maturity_date"), get("spot"), get("strike"), get("quantity"), get("barrier"), get("barrier_direction"), get("barrier_style"), get("risk_free_rate"), get("dividend_rate"), get("volatility"), get("paths", 1024))
    if product == "EQUITY_ASIAN_OPTION_NPV":
        return PYQUANTLIB_EQUITY_ASIAN_OPTION_NPV(get("option_type"), get("evaluation_date"), get("maturity_date"), get("spot"), get("strike"), get("quantity"), get("risk_free_rate"), get("dividend_rate"), get("volatility"), get("paths", 1024))
    if product == "EQUITY_TRS_NPV":
        return PYQUANTLIB_EQUITY_TRS_NPV(get("evaluation_date"), get("maturity_date"), get("notional"), get("spot"), get("initial_price"), get("risk_free_rate"), get("dividend_rate"), get("funding_rate"), get("funding_spread", 0.0), get("receive_equity", True), get("frequency_months", 3))
    if product == "COMMODITY_FORWARD_NPV":
        return PYQUANTLIB_COMMODITY_FORWARD_NPV(get("evaluation_date"), get("maturity_date"), get("spot"), get("quantity"), get("contract_price"), get("forward_rate"), get("discount_rate"), get("long_position", True))
    if product == "COMMODITY_SWAP_NPV":
        return PYQUANTLIB_COMMODITY_SWAP_NPV(get("evaluation_date"), get("maturity_date"), get("spot"), get("quantity"), get("fixed_price"), get("forward_rate"), get("discount_rate"), get("receive_floating", True), get("frequency_months", 1))
    if product == "COMMODITY_OPTION_NPV":
        return PYQUANTLIB_COMMODITY_OPTION_NPV(get("option_type"), get("evaluation_date"), get("maturity_date"), get("spot"), get("quantity"), get("strike"), get("forward_rate"), get("discount_rate"), get("volatility"))
    if product == "CDS_NPV":
        return PYQUANTLIB_CDS_NPV(get("evaluation_date"), get("maturity_date"), get("notional"), get("running_spread"), get("hazard_rate"), get("recovery_rate"), get("discount_rate"), get("buy_protection", True), get("frequency_months", 3))
    if product == "CDS_OPTION_NPV":
        return PYQUANTLIB_CDS_OPTION_NPV(get("option_type"), get("evaluation_date"), get("exercise_date"), get("maturity_date"), get("notional"), get("running_spread"), get("strike_spread"), get("hazard_rate"), get("recovery_rate"), get("discount_rate"), get("volatility"), get("buy_protection", True), get("frequency_months", 3))
    if product == "ZC_INFLATION_SWAP_NPV":
        return PYQUANTLIB_ZC_INFLATION_SWAP_NPV(get("evaluation_date"), get("maturity_date"), get("notional"), get("fixed_rate"), get("base_index"), get("inflation_rate"), get("discount_rate"), get("receive_inflation", True))
    if product == "YOY_INFLATION_SWAP_NPV":
        return PYQUANTLIB_YOY_INFLATION_SWAP_NPV(get("evaluation_date"), get("maturity_date"), get("notional"), get("fixed_rate"), get("base_index"), get("inflation_rate"), get("discount_rate"), get("receive_inflation", True), get("frequency_months", 12))
    if product == "VARIANCE_SWAP_NPV":
        return PYQUANTLIB_VARIANCE_SWAP_NPV(get("evaluation_date"), get("maturity_date"), get("strike_variance"), get("notional"), get("volatility"), get("discount_rate"), get("long_position", True))
    if product == "VOLATILITY_SWAP_NPV":
        return PYQUANTLIB_VOLATILITY_SWAP_NPV(get("evaluation_date"), get("maturity_date"), get("strike_volatility"), get("notional"), get("volatility"), get("discount_rate"), get("long_position", True))
    raise ValueError(f"unsupported product: {product}")


def _row_inputs(sheet, columns: dict[str, int], row: int) -> dict[str, object]:
    values = {}
    for name, col in columns.items():
        value = sheet.cells(row, col).value
        if value not in (None, ""):
            values[name] = value
    return values
