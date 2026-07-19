import unittest

import pandas as pd

from src.etl.prepare_datasets.global_flows import prepare_gf1_dataset, prepare_gf2_dataset, prepare_gf3_dataset


class GlobalFlowsPreparationTests(unittest.TestCase):
    def test_monthly_sterling_series_align_and_normalise(self):
        dates = pd.to_datetime(["2024-01-31", "2024-02-29"])
        frame = pd.DataFrame({"date": dates.tolist() * 3, "metric_id": ["STERLING_ERI_MO"] * 2 + ["USD_GBP_SPOT_MO"] * 2 + ["EUR_GBP_SPOT_MO"] * 2, "value": [100, 101, 1.2, 1.3, 1.1, 1.0]})
        result = prepare_gf1_dataset(frame)
        self.assertEqual(result["baseline_date"].iloc[0], pd.Timestamp("2024-01-31"))
        self.assertEqual(result.iloc[0]["USD_GBP_SPOT_MO_normalised"], 100.0)

    def test_daily_asset_common_baseline_and_oil_spread(self):
        dates = pd.date_range("2024-01-02", periods=3, freq="B")
        frame = pd.DataFrame({"date": dates.tolist() * 3, "metric_id": ["ETF_UK_GILT_close"] * 3 + ["ETF_UK_TIPS_close"] * 3 + ["COM_GOLD_close"] * 3, "value": [100, 101, 102, 90, 91, 92, 200, 201, 202]})
        result = prepare_gf2_dataset(frame)
        self.assertEqual(result["ETF_UK_GILT_close_normalised"].iloc[0], 100.0)
        self.assertTrue(pd.isna(result["ETF_UK_GILT_close_return_21d"]).all())

        oil = pd.DataFrame({"date": dates.tolist() * 2, "metric_id": ["COM_OIL_BRENT_close"] * 3 + ["COM_OIL_WTI_close"] * 3, "value": [80, 81, 82, 75, 76, 77]})
        oil_result = prepare_gf3_dataset(oil)
        self.assertEqual(oil_result["BRENT_WTI_SPREAD"].iloc[-1], 5)

    def test_missing_tips_remains_optional(self):
        dates = pd.date_range("2024-01-02", periods=2, freq="B")
        frame = pd.DataFrame({"date": dates.tolist() * 2, "metric_id": ["ETF_UK_GILT_close"] * 2 + ["COM_GOLD_close"] * 2, "value": [100, 101, 200, 202]})
        result = prepare_gf2_dataset(frame)
        self.assertIn("ETF_UK_TIPS_close", result.columns)
        self.assertTrue(result["ETF_UK_TIPS_close"].isna().all())


if __name__ == "__main__":
    unittest.main()
