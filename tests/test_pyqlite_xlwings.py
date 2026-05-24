from __future__ import annotations

import unittest
from datetime import date

from pyqlite_xlwings import (
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


class XlwingsWrapperTests(unittest.TestCase):
    def test_fx_forward_functions(self) -> None:
        evaluation_date = date(2026, 5, 22)
        maturity_date = date(2027, 5, 24)

        fair_rate = PYQL_FX_FORWARD_RATE(evaluation_date, maturity_date, 1.35, 0.04, 0.025)
        zero_npv_rate = PYQL_FX_FORWARD_ZERO_NPV_RATE(evaluation_date, maturity_date, 1.35, 0.04, 0.025)
        npv = PYQL_FX_FORWARD_NPV(
            evaluation_date,
            maturity_date,
            1.35,
            1_000_000.0,
            zero_npv_rate,
            0.04,
            0.025,
        )

        self.assertGreater(fair_rate, 0.0)
        self.assertGreater(zero_npv_rate, 0.0)
        self.assertAlmostEqual(npv, 0.0, places=7)

    def test_fx_option_function(self) -> None:
        value = PYQL_FX_OPTION_NPV(
            "CALL",
            date(2026, 5, 22),
            date(2027, 5, 22),
            1.25,
            1.27,
            1_000_000.0,
            0.04,
            0.02,
            0.15,
        )

        self.assertGreater(value, 0.0)

    def test_digital_fx_option_function(self) -> None:
        value = PYQL_DIGITAL_FX_OPTION_NPV(
            "CALL",
            date(2026, 5, 22),
            date(2027, 5, 22),
            1.25,
            1.27,
            1_000_000.0,
            1.0,
            0.04,
            0.02,
            0.15,
        )

        self.assertGreater(value, 0.0)

    def test_swap_functions(self) -> None:
        evaluation_date = date(2026, 5, 22)
        maturity_date = date(2031, 5, 22)

        fair_rate = PYQL_SWAP_FAIR_RATE(
            evaluation_date,
            maturity_date,
            1_000_000.0,
            0.035,
            0.035,
        )
        npv = PYQL_SWAP_NPV(
            evaluation_date,
            maturity_date,
            1_000_000.0,
            fair_rate,
            0.035,
            0.035,
        )

        self.assertGreater(fair_rate, 0.0)
        self.assertAlmostEqual(npv, 0.0, places=7)

    def test_ois_and_basis_swap_functions(self) -> None:
        evaluation_date = date(2026, 5, 22)
        maturity_date = date(2031, 5, 22)

        fair_ois = PYQL_OIS_FAIR_RATE(
            evaluation_date,
            maturity_date,
            1_000_000.0,
            0.035,
            0.034,
        )
        ois_npv = PYQL_OIS_NPV(
            evaluation_date,
            maturity_date,
            1_000_000.0,
            fair_ois,
            0.035,
            0.034,
        )
        basis_npv = PYQL_FLOAT_FLOAT_NPV(
            evaluation_date,
            maturity_date,
            1_000_000.0,
            1_000_000.0,
            0.035,
            0.033,
            0.036,
            0.0,
            0.001,
        )

        self.assertGreater(fair_ois, 0.0)
        self.assertAlmostEqual(ois_npv, 0.0, places=7)
        self.assertNotEqual(basis_npv, 0.0)

    def test_nonstandard_swap_function(self) -> None:
        npv = PYQL_NONSTANDARD_SWAP_NPV(
            date(2026, 5, 22),
            date(2028, 5, 22),
            "1000000,900000,800000,700000",
            "1000000,900000,800000,700000",
            "0.033,0.034,0.035,0.036",
            0.035,
            0.034,
            True,
            6,
            "1,1,1,1",
            "0.001,0.001,0.001,0.001",
            True,
            True,
        )

        self.assertNotEqual(npv, 0.0)

    def test_additional_ir_products(self) -> None:
        fra = PYQL_FRA_NPV(
            date(2026, 5, 22),
            date(2026, 11, 24),
            date(2027, 5, 24),
            1_000_000.0,
            0.0325,
            0.035,
            0.035,
        )
        bond = PYQL_FIXED_BOND_NPV(
            date(2026, 5, 22),
            date(2029, 5, 22),
            100.0,
            0.05,
            0.04,
        )
        cap = PYQL_CAPFLOOR_NPV(
            "CAP",
            date(2026, 5, 22),
            date(2026, 11, 24),
            date(2028, 11, 24),
            1_000_000.0,
            0.04,
            "",
            0.035,
            0.035,
            0.20,
        )
        swaption = PYQL_SWAPTION_NPV(
            date(2026, 5, 22),
            date(2027, 5, 24),
            date(2032, 5, 24),
            1_000_000.0,
            0.0375,
            0.035,
            0.035,
            0.18,
        )

        self.assertNotEqual(fra, 0.0)
        self.assertGreater(bond, 0.0)
        self.assertGreater(cap, 0.0)
        self.assertGreater(swaption, 0.0)

    def test_swaption_matrix_vol_spec_is_accepted(self) -> None:
        value = PYQL_SWAPTION_NPV(
            date(2026, 5, 22),
            date(2027, 5, 24),
            date(2032, 5, 24),
            1_000_000.0,
            0.0375,
            0.035,
            0.035,
            "matrix|1Y,2Y|5Y,10Y|0.18,0.19;0.20,0.21",
        )

        self.assertGreater(value, 0.0)

    def test_excel_csv_style_values_are_accepted(self) -> None:
        fair_rate = PYQL_SWAP_FAIR_RATE(
            "2026-05-22",
            "2031-05-22",
            "1000000",
            "0.035",
            "0.035",
            "TRUE",
            "",
            "",
            "",
        )
        npv = PYQL_SWAP_NPV(
            "2026-05-22",
            "2031-05-22",
            "1000000",
            fair_rate,
            "0.035",
            "0.035",
            "TRUE",
            "",
            "",
            "",
        )

        self.assertGreater(fair_rate, 0.0)
        self.assertAlmostEqual(npv, 0.0, places=7)

    def test_excel_two_digit_century_date_is_repaired_for_maturity(self) -> None:
        fair_rate = PYQL_SWAP_FAIR_RATE(
            date(2026, 5, 22),
            date(1931, 5, 22),
            1_000_000,
            0.035,
            0.035,
            True,
        )

        self.assertGreater(fair_rate, 0.0)

    def test_curve_and_surface_specs_are_accepted(self) -> None:
        option_value = PYQL_FX_OPTION_NPV(
            "CALL",
            "2026-05-22",
            "2028-05-22",
            1.25,
            1.27,
            1_000_000,
            0.04,
            0.02,
            0.15,
            "2027-05-22:0.039;2029-05-22:0.041",
            "2027-05-22:0.024;2029-05-22:0.027",
            "-0.25,ATM,0.25|2027-05-22:0.17,0.15,0.16|2029-05-22:0.19,0.165,0.18",
        )
        fair_rate = PYQL_SWAP_FAIR_RATE(
            "2026-05-22",
            "2031-05-22",
            1_000_000,
            0.035,
            0.035,
            True,
            6,
            6,
            0.0,
            "2027-05-22:0.033;2029-05-22:0.036;2031-05-22:0.038",
            "2027-05-22:0.034;2029-05-22:0.037;2031-05-22:0.039",
        )

        self.assertGreater(option_value, 0.0)
        self.assertGreater(fair_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
