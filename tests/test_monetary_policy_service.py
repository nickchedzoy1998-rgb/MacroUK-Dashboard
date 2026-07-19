import unittest

import pandas as pd

from src.api.services.monetary_policy import build_monetary_policy_insights, build_monetary_policy_summary


def kpi(kpi_id, value, delta=None):
    return {"kpi_id": kpi_id, "value": value, "delta": delta}


class MonetaryPolicyServiceTests(unittest.TestCase):
    def test_summary_handles_missing_optional_gilt_data(self):
        summary = build_monetary_policy_summary([
            kpi("BANK_RATE", 3.75, -0.25),
            kpi("BANK_RATE_SONIA_SPREAD", 0.02, 0.01),
            kpi("M4_GROWTH_MO", 4.8, 0.2),
        ])
        self.assertIn("restrictive", summary["headline"])
        self.assertIn("close to Bank Rate", summary["headline"])

    def test_mixed_money_growth_is_neutral(self):
        datasets = {
            "MP1": pd.DataFrame({"date": ["2024-01-01"], "BANK_RATE_DA": [4.0], "SONIA": [3.9], "BANK_RATE_SONIA_SPREAD": [0.1]}),
            "MP2": pd.DataFrame({"date": ["2024-01-31", "2024-02-29"], "M4_GROWTH_MO": [2.0, 2.5], "NOTES_COINS_GROWTH_MO": [4.0, 3.5]}),
            "MP3": pd.DataFrame({"date": ["2024-01-31"], "CORP_OVERDRAFT_COST_MO": [5.0], "NET_LENDING_CORP_MO": [-1.0]}),
        }
        insights = build_monetary_policy_insights(datasets)
        self.assertEqual(next(item for item in insights if item["chart_id"] == "MP2")["direction"], "neutral")


if __name__ == "__main__":
    unittest.main()
