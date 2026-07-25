import unittest

import pandas as pd

from src.api.services.financial_markets import build_financial_markets_insights, build_financial_markets_summary


class FinancialMarketsServiceTests(unittest.TestCase):
    def test_summary_uses_cautious_market_language(self):
        kpis = [
            {"kpi_id": "FTSE_100", "value": 2.0},
            {"kpi_id": "FTSE_250", "value": 1.0},
            {"kpi_id": "FTSE_250_RELATIVE", "value": -1.0},
        ]
        summary = build_financial_markets_summary(kpis)
        self.assertIn("tracked large and mid-cap indices", summary["headline"])
        self.assertIn("does not represent a complete measure", summary["body"])

    def test_insight_ranks_available_proxies_and_tolerates_missing_company(self):
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-07-10"]),
                "EQ_BARC_close_return_21d": [1.0],
                "EQ_BP_close_return_21d": [None],
                "EQ_RIO_close_return_21d": [3.0],
                "EQ_GSK_close_return_21d": [-2.0],
            }
        )
        insights = build_financial_markets_insights({"FM3": frame})
        self.assertEqual(len(insights), 1)
        self.assertIn("Rio Tinto", insights[0]["body"])
        self.assertIn("GSK", insights[0]["body"])
        self.assertNotIn("EQ_", insights[0]["body"])


if __name__ == "__main__":
    unittest.main()
