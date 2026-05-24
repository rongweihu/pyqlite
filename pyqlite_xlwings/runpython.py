from __future__ import annotations

try:
    import xlwings as xw
except ImportError as exc:
    raise RuntimeError("pyqlite_xlwings.runpython requires xlwings to be installed") from exc

from pyqlite_xlwings.functions import (
    PYQL_CAPFLOOR_NPV,
    PYQL_DIGITAL_FX_OPTION_NPV,
    PYQL_FIXED_BOND_NPV,
    PYQL_FLOAT_FLOAT_NPV,
    PYQL_FRA_NPV,
    PYQL_FX_FORWARD_NPV,
    PYQL_FX_FORWARD_RATE,
    PYQL_FX_FORWARD_ZERO_NPV_RATE,
    PYQL_FX_OPTION_NPV,
    PYQL_NONSTANDARD_SWAP_NPV,
    PYQL_OIS_FAIR_RATE,
    PYQL_OIS_NPV,
    PYQL_SWAPTION_NPV,
    PYQL_SWAP_FAIR_RATE,
    PYQL_SWAP_NPV,
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
        return PYQL_FX_FORWARD_RATE(
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
        return PYQL_FX_FORWARD_ZERO_NPV_RATE(
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
        return PYQL_FX_FORWARD_NPV(
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
        return PYQL_FX_OPTION_NPV(
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
        return PYQL_DIGITAL_FX_OPTION_NPV(
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
        return PYQL_FRA_NPV(
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
        return PYQL_FIXED_BOND_NPV(
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
        return PYQL_CAPFLOOR_NPV(
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
        return PYQL_SWAPTION_NPV(
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
        return PYQL_SWAP_FAIR_RATE(
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
        return PYQL_SWAP_NPV(
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
        return PYQL_OIS_NPV(
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
        return PYQL_OIS_FAIR_RATE(
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
        return PYQL_FLOAT_FLOAT_NPV(
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
        return PYQL_NONSTANDARD_SWAP_NPV(
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
    raise ValueError(f"unsupported product: {product}")


def _row_inputs(sheet, columns: dict[str, int], row: int) -> dict[str, object]:
    values = {}
    for name, col in columns.items():
        value = sheet.cells(row, col).value
        if value not in (None, ""):
            values[name] = value
    return values
