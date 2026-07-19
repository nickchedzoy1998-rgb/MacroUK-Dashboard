import sqlite3
import unittest

import pandas as pd
from fastapi import HTTPException

from src.api.routers.macro_pulse import get_macro_pulse_summary
from src.api.schemas.macro_pulse import MacroPulseResponse
from src.api.services.macro_pulse_api import MacroPulseDataError, build_macro_pulse_response


def build_fixture(*, empty_labour: bool = False, omit_growth: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    tables = {
        "chart_macropulse_egm": pd.DataFrame(
            {
                "date": ["2024-03-31", "2024-06-30", "2024-12-31"],
                "GDP_QOQ": [-0.2, 0.1, None],
                "GDP_YOY": [None, None, 1.2],
                "chart": ["EGM"] * 3,
            }
        ),
        "chart_macropulse_ib": pd.DataFrame(
            {
                "date": ["2024-01-31", "2024-02-29"],
                "CPI": [2.8, 2.7],
                "CORE_CPI": [3.4, None],
                "chart": ["IB"] * 2,
            }
        ),
        "chart_macropulse_lbh": pd.DataFrame(
            {
                "date": [] if empty_labour else ["2024-01-31", "2024-02-29"],
                "UNRATE": [] if empty_labour else [4.5, 4.7],
                "EMPRATE": [] if empty_labour else [74.0, 74.2],
                "WAGE_GROWTH": [] if empty_labour else [5.0, 4.8],
                "chart": [] if empty_labour else ["LBH", "LBH"],
            }
        ),
    }
    if omit_growth:
        tables.pop("chart_macropulse_egm")
    for table, dataframe in tables.items():
        dataframe.to_sql(table, conn, index=False)

    pd.DataFrame(
        {
            "date": [
                "2024-01-01", "2024-04-01", "2024-01-01", "2024-01-01",
                "2024-01-01", "2024-02-01", "2024-03-01",
            ],
            "metric_id": [
                "GDP_QOQ", "GDP_QOQ", "CPI", "UNRATE",
                "UNRATE", "UNRATE", "WAGE_GROWTH",
            ],
            "value": [0.2, 0.4, 2.2, 4.5, 4.6, 4.7, 4.0],
            "frequency": ["Quarterly", "Quarterly", "Monthly", "Monthly", "Monthly", "Monthly", "Monthly"],
        }
    ).to_sql("economic_series", conn, index=False)
    return conn


class MacroPulseApiTests(unittest.TestCase):
    def test_successful_response_is_valid_and_ordered(self):
        conn = build_fixture()
        response = build_macro_pulse_response(conn)
        conn.close()

        self.assertIsInstance(response, MacroPulseResponse)
        self.assertEqual(response.page.id, "macro_pulse")
        self.assertEqual([chart.id for chart in response.charts], ["EGM", "IB", "LBH"])
        self.assertEqual(response.charts[0].series_metadata[0].role, "bar")
        self.assertEqual(response.charts[0].series_metadata[1].role, "line")
        self.assertEqual(response.charts[0].records[0].values["GDP_QOQ"], -0.2)
        self.assertTrue(response.kpis[0].date.isoformat())
        payload = response.model_dump(mode="json")
        self.assertEqual(payload["charts"][0]["records"][0]["date"], "2024-03-31")
        self.assertIn("headline", payload["summary"])

    def test_optional_series_is_missing_without_invalidating_chart(self):
        conn = build_fixture()
        response = build_macro_pulse_response(conn)
        conn.close()

        inflation = response.charts[1]
        self.assertIn("HOUSE_PRICE_GROWTH", inflation.coverage.missing_metrics)
        self.assertTrue(next(series for series in inflation.series_metadata if series.metric == "HOUSE_PRICE_GROWTH").optional)
        self.assertEqual(inflation.target, 2.0)
        self.assertIsNotNone(inflation.records)

    def test_empty_chart_keeps_page_response_valid_and_insight_optional(self):
        conn = build_fixture(empty_labour=True)
        response = build_macro_pulse_response(conn)
        conn.close()

        labour = response.charts[2]
        self.assertEqual(labour.records, [])
        self.assertIsNone(labour.insight)
        self.assertEqual(labour.coverage.available_metrics, [])

    def test_missing_required_table_raises_internal_data_error_and_route_hides_details(self):
        conn = build_fixture(omit_growth=True)
        with self.assertRaises(MacroPulseDataError):
            build_macro_pulse_response(conn)
        with self.assertRaises(HTTPException) as context:
            get_macro_pulse_summary(conn)
        conn.close()
        self.assertEqual(context.exception.status_code, 503)
        self.assertNotIn("Traceback", context.exception.detail)
        self.assertNotIn("chart_macropulse_egm", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
