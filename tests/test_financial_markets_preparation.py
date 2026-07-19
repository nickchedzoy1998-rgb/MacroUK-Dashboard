import unittest

import pandas as pd

from src.analytics.chart_transforms import year_to_date_return
from src.etl.prepare_datasets.financial_markets import (
    prepare_fm1_dataset,
    prepare_fm2_monthly_dataset,
    prepare_fm3_dataset,
)


def long_frame(metrics, dates, values):
    rows = []
    for metric, series in values.items():
        rows.extend({"date": date, "metric_id": metric, "value": value} for date, value in zip(dates, series))
    return pd.DataFrame(rows)


class FinancialMarketsPreparationTests(unittest.TestCase):
    def test_fm1_common_baseline_and_trading_observation_returns(self):
        dates = pd.date_range("2024-01-02", periods=65, freq="B")
        frame = long_frame(
            (), dates,
            {"FTSE_100_close": range(100, 165), "FTSE_250_close": range(200, 265), "FTSE_AIM_close": range(300, 365)},
        )
        result = prepare_fm1_dataset(frame)
        self.assertEqual(result["baseline_date"].iloc[0], dates[0])
        self.assertAlmostEqual(result.loc[21, "FTSE_100_close_return_21d"], ((121 / 100) - 1) * 100)
        self.assertTrue(pd.isna(result.loc[0, "FTSE_100_close_return_21d"]))

    def test_year_to_date_uses_prior_year_last_observation(self):
        frame = pd.DataFrame({"date": pd.to_datetime(["2023-12-29", "2024-01-02", "2024-02-01"]), "metric_id": "A", "value": [100, 110, 120]})
        result = year_to_date_return(frame)
        self.assertAlmostEqual(result.iloc[-1]["return_pct"], 20.0)

    def test_fm2_monthly_does_not_forward_fill_hpi_to_daily_dates(self):
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-02", "2024-01-31", "2024-02-01", "2024-02-29", "2024-01-02", "2024-01-31", "2024-02-01", "2024-02-29", "2024-01-31", "2024-02-29"]),
                "metric_id": ["EQ_TW_close", "EQ_TW_close", "EQ_TW_close", "EQ_TW_close", "EQ_BAR_close", "EQ_BAR_close", "EQ_BAR_close", "EQ_BAR_close", "UK_HPI_INDEX_UK", "UK_HPI_INDEX_UK"],
                "value": [100, 110, 112, 120, 90, 95, 96, 100, 100, 105],
            }
        )
        result = prepare_fm2_monthly_dataset(frame)
        self.assertEqual(result["date"].tolist(), list(pd.to_datetime(["2024-01-31", "2024-02-29"])))
        self.assertEqual(result["baseline_date"].iloc[0], pd.Timestamp("2024-01-31"))

    def test_fm3_keeps_missing_history_as_missing_returns(self):
        dates = pd.date_range("2024-01-02", periods=3, freq="B")
        frame = long_frame(
            (), dates,
            {metric: [100, 101, 102] for metric in ("EQ_BARC_close", "EQ_BP_close", "EQ_RIO_close", "EQ_GSK_close", "SGE_L_close")},
        )
        result = prepare_fm3_dataset(frame)
        self.assertTrue(result["EQ_BARC_close_return_21d"].isna().all())


if __name__ == "__main__":
    unittest.main()
