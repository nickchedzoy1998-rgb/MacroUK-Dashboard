import unittest

import pandas as pd

from src.etl.prepare_datasets.monetary_policy import (
    prepare_mp1_dataset,
    prepare_mp2_dataset,
    prepare_mp3_dataset,
)


class MonetaryPolicyPreparationTests(unittest.TestCase):
    def test_mp1_aligns_daily_rates_and_calculates_spread(self):
        frame = pd.DataFrame({"date": ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"], "metric_id": ["BANK_RATE_DA", "SONIA", "BANK_RATE_DA", "SONIA"], "value": [5.25, 5.2, 5.25, 5.1]})
        result = prepare_mp1_dataset(frame)
        self.assertEqual(result["BANK_RATE_SONIA_SPREAD"].tolist(), [0.04999999999999982, 0.15000000000000036])

    def test_optional_gilt_is_price_column_not_yield(self):
        frame = pd.DataFrame({"date": ["2024-01-02", "2024-01-02", "2024-01-02"], "metric_id": ["BANK_RATE_DA", "SONIA", "ETF_UK_GILT_close"], "value": [5.25, 5.2, 9.8]})
        result = prepare_mp1_dataset(frame)
        self.assertIn("ETF_UK_GILT_close", result.columns)
        self.assertNotIn("GILT_YIELD", result.columns)

    def test_monthly_tables_preserve_negative_values_and_null_gaps(self):
        mp2 = prepare_mp2_dataset(pd.DataFrame({"date": ["2024-01-01", "2024-02-01", "2024-02-01"], "metric_id": ["M4_GROWTH_MO", "M4_GROWTH_MO", "NOTES_COINS_GROWTH_MO"], "value": [-1.2, -0.5, 2.0]}))
        self.assertEqual(mp2.loc[mp2["M4_GROWTH_MO"].notna(), "M4_GROWTH_MO"].tolist(), [-1.2, -0.5])
        self.assertTrue(pd.isna(mp2.loc[mp2["date"] == pd.Timestamp("2024-01-31"), "NOTES_COINS_GROWTH_MO"]).all())

        mp3 = prepare_mp3_dataset(pd.DataFrame({"date": ["2024-01-31", "2024-01-31"], "metric_id": ["CORP_OVERDRAFT_COST_MO", "NET_LENDING_CORP_MO"], "value": [5.0, -4.0]}))
        self.assertEqual(mp3.loc[0, "NET_LENDING_CORP_MO"], -4.0)


if __name__ == "__main__":
    unittest.main()
