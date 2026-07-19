import unittest

import pandas as pd

from src.etl.prepare_datasets.housing_credit import prepare_hc1_dataset, prepare_hc2_dataset, prepare_hc3_dataset, prepare_hc4_dataset


class HousingCreditPreparationTests(unittest.TestCase):
    def test_hc1_monthly_gaps_are_preserved(self):
        result = prepare_hc1_dataset(pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "metric_id": ["MORTGAGE_2YR_75LTV_MO", "UK_HPI_YOY_CHANGE_UK"], "value": [4.0, -1.0]}))
        self.assertTrue(pd.isna(result.loc[0, "UK_HPI_YOY_CHANGE_UK"]))

    def test_hc2_returns_common_baseline_and_rebased_values(self):
        frame = pd.DataFrame({"date": ["2024-01-01", "2024-02-01", "2024-02-01", "2024-02-01", "2024-01-01"], "metric_id": ["UK_HPI_AVG_PRICE_UK", "UK_HPI_AVG_PRICE_UK", "UK_HPI_AVG_PRICE_LONDON", "UK_HPI_AVG_PRICE_NW", "UK_HPI_AVG_PRICE_LONDON"], "value": [100, 110, 220, 150, 200]})
        result = prepare_hc2_dataset(frame)
        self.assertEqual(result["baseline_date"].iloc[0], pd.Timestamp("2024-02-29"))
        self.assertEqual(result.loc[result.date == pd.Timestamp("2024-02-29"), "UK_HPI_AVG_PRICE_UK_normalised"].iloc[0], 100.0)

    def test_hc3_uses_only_ew_components_and_calculates_cash_share(self):
        result = prepare_hc3_dataset(pd.DataFrame({"date": ["2024-01-01", "2024-01-01"], "metric_id": ["UK_HPI_CASH_SALES_VOL", "UK_HPI_MORTGAGE_SALES_VOL"], "value": [40, 60]}))
        self.assertNotIn("UK_HPI_VOLUME_UK", result.columns)
        self.assertEqual(result.loc[0, "EW_TOTAL_TRANSACTIONS"], 100)
        self.assertEqual(result.loc[0, "CASH_SHARE_PCT"], 40)

    def test_hc4_preserves_negative_lending(self):
        result = prepare_hc4_dataset(pd.DataFrame({"date": ["2024-01-01", "2024-01-01"], "metric_id": ["NET_LENDING_DWELLINGS_MO", "NET_CONSUMER_CREDIT_MO"], "value": [-100, 20]}))
        self.assertEqual(result.loc[0, "NET_LENDING_DWELLINGS_MO"], -100)


if __name__ == "__main__":
    unittest.main()
