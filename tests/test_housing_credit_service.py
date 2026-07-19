import unittest

import pandas as pd

from src.api.services.housing_credit import build_housing_credit_insights, build_housing_credit_summary


class HousingCreditServiceTests(unittest.TestCase):
    def test_summary_tolerates_missing_transactions(self):
        summary = build_housing_credit_summary([{"kpi_id": "MORTGAGE_RATE", "value": 4.5, "delta": -0.1}, {"kpi_id": "HOUSE_PRICE_GROWTH", "value": 0.7, "delta": 0.2}], None)
        self.assertIn("mortgage", summary["headline"].lower())

    def test_mixed_borrowing_signals_are_neutral(self):
        insights = build_housing_credit_insights({"HC4": pd.DataFrame({"date": ["2024-01-31"], "NET_LENDING_DWELLINGS_MO": [100], "NET_CONSUMER_CREDIT_MO": [-20]})})
        self.assertEqual(insights[0]["direction"], "neutral")


if __name__ == "__main__":
    unittest.main()
