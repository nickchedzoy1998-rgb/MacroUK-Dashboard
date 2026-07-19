import unittest
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from src.etl.prepare_datasets.macro_pulse import (
    prepare_growth_dataset,
    prepare_inflation_dataset,
    prepare_labour_dataset,
    prepare_macro_pulse_kpis,
)


class MacroPulsePreparationTests(unittest.TestCase):
    def test_growth_is_native_frequency_sorted_and_preserves_negative_values(self):
        frame = pd.DataFrame(
            {
                "date": ["2025-01-01", "2024-10-01", "2024-01-01", "2024-01-01"],
                "metric_id": ["GDP_YOY", "GDP_QOQ", "GDP_QOQ", "GDP_YOY"],
                "value": [1.2, -0.2, 0.3, 0.9],
            }
        )
        result = prepare_growth_dataset(frame)
        self.assertEqual(result["date"].tolist(), list(pd.to_datetime(["2024-03-31", "2024-12-31", "2025-12-31"])))
        self.assertEqual(result.loc[result["GDP_QOQ"].notna(), "GDP_QOQ"].tolist(), [0.3, -0.2])
        self.assertFalse((result.fillna(0) == 0).all(axis=None))

    def test_inflation_aligns_monthly_and_optional_housing_metric_is_not_substituted(self):
        frame = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-02-01", "2024-02-01", "2023-01-01", "2024-01-01", "2024-01-01"],
                "metric_id": ["CPI", "CPI", "CORE_CPI", "CORE_CPI", "CORE_CPI", "HOUSE_PRICE_GROWTH"],
                "value": [4.0, 4.1, 105.0, 100.0, 104.0, 2.0],
            }
        )
        result = prepare_inflation_dataset(frame)
        self.assertEqual(result["date"].tolist(), list(pd.to_datetime(["2024-01-31", "2024-02-29"])))
        self.assertEqual(result.loc[result["date"] == pd.Timestamp("2024-02-29"), "CPI"].iloc[0], 4.1)
        self.assertTrue(pd.isna(result.loc[result["date"] == pd.Timestamp("2024-02-29"), "CORE_CPI"]).all())
        self.assertAlmostEqual(result.loc[result["date"] == pd.Timestamp("2024-01-31"), "CORE_CPI"].iloc[0], 4.0)
        self.assertEqual(result.loc[result["date"] == pd.Timestamp("2024-01-31"), "HOUSE_PRICE_GROWTH"].iloc[0], 2.0)

    def test_labour_partial_coverage_remains_null_without_forward_fill(self):
        frame = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-02-01", "2024-02-01"],
                "metric_id": ["UNRATE", "EMPRATE", "WAGE_GROWTH"],
                "value": [4.5, 74.0, 5.2],
            }
        )
        result = prepare_labour_dataset(frame)
        self.assertTrue(pd.isna(result.loc[result["date"] == pd.Timestamp("2024-02-29"), "UNRATE"]).all())
        self.assertEqual(result.loc[result["date"] == pd.Timestamp("2024-02-29"), "WAGE_GROWTH"].iloc[0], 5.2)

    def test_kpis_reuse_explicit_comparison_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "macro.db"
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE economic_series (date TEXT, metric_id TEXT, value REAL, frequency TEXT)")
            conn.executemany(
                "INSERT INTO economic_series VALUES (?, ?, ?, ?)",
                [
                    ("2024-01-01", "GDP_QOQ", 0.2, "Quarterly"),
                    ("2024-04-01", "GDP_QOQ", 0.4, "Quarterly"),
                    ("2024-01-01", "CPI", 2.2, "Monthly"),
                    ("2024-02-01", "UNRATE", 4.6, "Monthly"),
                    ("2024-03-01", "UNRATE", 4.8, "Monthly"),
                    ("2024-03-01", "WAGE_GROWTH", 4.0, "Monthly"),
                ],
            )
            conn.commit()
            rows = prepare_macro_pulse_kpis(conn)
            conn.close()

        mapped = {row["kpi_id"]: row for row in rows}
        self.assertEqual(mapped["GDP_GROWTH"]["delta"], 0.2)
        self.assertAlmostEqual(mapped["UNEMPLOYMENT"]["delta"], 0.2)
        self.assertEqual(mapped["UNEMPLOYMENT"]["delta_direction"], "inverse")
        self.assertIsNone(mapped["WAGE_GROWTH"]["delta"])


if __name__ == "__main__":
    unittest.main()
