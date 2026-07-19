import unittest

import pandas as pd

from src.api.services.macro_pulse import (
    build_macro_pulse_insights,
    build_macro_pulse_summary,
    growth_state,
    inflation_state,
)


def kpi(kpi_id, value=None, delta=None):
    return {"kpi_id": kpi_id, "value": value, "delta": delta}


class MacroPulseServiceTests(unittest.TestCase):
    def test_named_growth_and_inflation_thresholds(self):
        self.assertEqual(growth_state(-0.1), "contracting")
        self.assertEqual(growth_state(0.1), "broadly flat")
        self.assertEqual(growth_state(0.3), "growing modestly")
        self.assertEqual(growth_state(0.6), "showing stronger growth")
        self.assertEqual(inflation_state(3.1), "materially above target")
        self.assertEqual(inflation_state(2.1), "near target")

    def test_summary_handles_missing_component_and_wage_easing(self):
        summary = build_macro_pulse_summary(
            [kpi("GDP_GROWTH", -0.2), kpi("WAGE_GROWTH", 4.5, -0.2)],
        )
        self.assertIn("contracting", summary["headline"])
        self.assertIn("wage growth is easing", summary["body"].lower())
        self.assertNotIn("spiral", summary["body"].lower())

    def test_mixed_labour_signals_are_neutral(self):
        datasets = {
            "EGM": pd.DataFrame({"date": ["2024-01-01", "2024-04-01"], "GDP_QOQ": [0.1, 0.3], "GDP_YOY": [1.0, 1.2]}),
            "IB": pd.DataFrame({"date": ["2024-01-31"], "CPI": [2.1], "CORE_CPI": [2.4]}),
            "LBH": pd.DataFrame({"date": ["2024-01-31", "2024-02-29"], "UNRATE": [4.5, 4.7], "EMPRATE": [74.0, 74.2], "WAGE_GROWTH": [5.0, 4.8]}),
        }
        insights = build_macro_pulse_insights(datasets)
        labour = next(item for item in insights if item["chart_id"] == "LBH")
        self.assertEqual(labour["direction"], "neutral")

    def test_insights_have_expected_chart_ids_and_no_missing_data_claim(self):
        datasets = {
            "EGM": pd.DataFrame({"date": ["2024-01-01"], "GDP_QOQ": [-0.2], "GDP_YOY": [None]}),
            "IB": pd.DataFrame({"date": ["2024-01-31"], "CPI": [None], "CORE_CPI": [2.0]}),
            "LBH": pd.DataFrame({"date": ["2024-01-31"], "UNRATE": [4.5], "EMPRATE": [None], "WAGE_GROWTH": [None]}),
        }
        insights = build_macro_pulse_insights(datasets)
        self.assertEqual({item["chart_id"] for item in insights}, {"EGM", "IB", "LBH"})
        self.assertNotIn("None", " ".join(item["body"] for item in insights))


if __name__ == "__main__":
    unittest.main()
