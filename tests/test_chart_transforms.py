import unittest

import pandas as pd

from src.analytics.chart_transforms import (
    coverage_report,
    cumulative_percentage_return,
    latest_observation_dates,
    latest_observations,
    normalise_to_common_baseline,
    previous_distinct_observations,
    previous_observations,
    prepare_time_series,
    resample_market_data_monthly,
    return_over_observations,
)


def series_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-02-01", "2024-01-01", "2024-02-01", "bad", "2024-01-01", "2024-03-01"],
            "metric_id": ["A", "A", "B", "A", "B", "A"],
            "value": [120, 100, 50, 99, 25, 150],
        }
    )


class ChartTransformTests(unittest.TestCase):
    def test_prepare_sorts_drops_invalid_and_does_not_mutate(self):
        source = series_frame()
        prepared = prepare_time_series(source)
        self.assertEqual(source.loc[0, "date"], "2024-02-01")
        self.assertEqual(prepared["date"].tolist(), list(pd.to_datetime(["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01", "2024-03-01"])))

    def test_normalisation_uses_first_common_date_and_handles_missing_early_values(self):
        frame = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-02-01", "2024-02-01", "2024-03-01", "2024-03-01"],
                "metric_id": ["A", "A", "B", "A", "B"],
                "value": [100, 110, 50, 120, 75],
            }
        )
        result, baseline = normalise_to_common_baseline(frame, metrics=["A", "B"])
        self.assertEqual(baseline, pd.Timestamp("2024-02-01"))
        values = result[result["date"] == baseline].set_index("metric_id")["normalised_value"]
        self.assertEqual(values.to_dict(), {"A": 100.0, "B": 100.0})

    def test_normalisation_safely_handles_no_common_date_and_zero_baseline(self):
        no_common = pd.DataFrame({"date": ["2024-01-01"], "metric_id": ["A"], "value": [1]})
        result, baseline = normalise_to_common_baseline(no_common, metrics=["A", "B"])
        self.assertTrue(result.empty)
        self.assertIsNone(baseline)

        zero = pd.DataFrame({"date": ["2024-01-01", "2024-01-01"], "metric_id": ["A", "B"], "value": [0, 10]})
        result, baseline = normalise_to_common_baseline(zero, metrics=["A", "B"])
        self.assertTrue(result.empty)
        self.assertIsNone(baseline)

    def test_cumulative_returns_and_missing_baseline(self):
        frame = pd.DataFrame(
            {"date": ["2024-01-01", "2024-02-01", "2024-01-01", "2024-02-01"], "metric_id": ["A", "A", "B", "B"], "value": [100, 125, 50, 60]}
        )
        result, baseline = cumulative_percentage_return(frame, metrics=["A", "B"])
        self.assertEqual(baseline, pd.Timestamp("2024-01-01"))
        self.assertEqual(result[result["metric_id"] == "A"].iloc[-1]["return_pct"], 25.0)

        missing, missing_date = cumulative_percentage_return(frame, metrics=["A", "B"], baseline_date="2024-03-01")
        self.assertTrue(missing.empty)
        self.assertIsNone(missing_date)

    def test_latest_previous_and_previous_distinct(self):
        frame = pd.DataFrame(
            {"date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-01-01"]), "metric_id": ["A", "A", "A", "B"], "value": [1, 1, 3, 4]}
        )
        self.assertEqual(latest_observations(frame).set_index("metric_id").loc["A", "value"], 3)
        self.assertEqual(previous_observations(frame).set_index("metric_id").loc["A", "value"], 1)
        self.assertEqual(previous_distinct_observations(frame).set_index("metric_id").loc["A", "value"], 1)
        self.assertEqual(latest_observation_dates(frame).set_index("metric_id").loc["A", "date"], pd.Timestamp("2024-03-01"))

    def test_observation_returns_and_monthly_resampling(self):
        frame = pd.DataFrame(
            {"date": pd.to_datetime(["2024-01-02", "2024-01-31", "2024-02-01", "2024-02-29"]), "metric_id": ["A"] * 4, "value": [100, 110, 120, 130]}
        )
        returns = return_over_observations(frame, 1)
        self.assertEqual(returns.iloc[-1]["return_pct"], (130 / 120 - 1) * 100)
        monthly = resample_market_data_monthly(frame)
        self.assertEqual(monthly["value"].tolist(), [110, 130])

    def test_coverage_reports_present_missing_and_dates(self):
        report = coverage_report(series_frame(), ["A", "B", "C"])
        self.assertEqual(report["present_metrics"], ["A", "B"])
        self.assertEqual(report["missing_metrics"], ["C"])
        self.assertEqual(report["valid_observations"]["A"], 3)
        self.assertEqual(report["first_valid_date"]["B"], pd.Timestamp("2024-01-01"))


if __name__ == "__main__":
    unittest.main()
