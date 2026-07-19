import sqlite3
import unittest

import pandas as pd

from src.api.services.housing_credit_api import build_housing_credit_response


class HousingCreditApiTests(unittest.TestCase):
    def test_response_order_baseline_and_geography(self):
        conn = sqlite3.connect(":memory:")
        tables = {
            "chart_housing_credit_hc1": {"date": ["2024-01-31"], "MORTGAGE_2YR_75LTV_MO": [4.0], "UK_HPI_YOY_CHANGE_UK": [1.0]},
            "chart_housing_credit_hc2": {"date": ["2024-01-31"], "UK_HPI_AVG_PRICE_UK": [100], "UK_HPI_AVG_PRICE_LONDON": [200], "UK_HPI_AVG_PRICE_NW": [150], "UK_HPI_AVG_PRICE_UK_normalised": [100], "UK_HPI_AVG_PRICE_LONDON_normalised": [100], "UK_HPI_AVG_PRICE_NW_normalised": [100], "baseline_date": ["2024-01-31"]},
            "chart_housing_credit_hc3": {"date": ["2024-01-31"], "UK_HPI_CASH_SALES_VOL": [40], "UK_HPI_MORTGAGE_SALES_VOL": [60], "EW_TOTAL_TRANSACTIONS": [100], "CASH_SHARE_PCT": [40]},
            "chart_housing_credit_hc4": {"date": ["2024-01-31"], "NET_LENDING_DWELLINGS_MO": [100], "NET_CONSUMER_CREDIT_MO": [-20]},
        }
        for table, data in tables.items(): pd.DataFrame(data).to_sql(table, conn, index=False)
        pd.DataFrame({"date": ["2024-01-31", "2024-01-31", "2024-01-31"], "metric_id": ["MORTGAGE_2YR_75LTV_MO", "UK_HPI_YOY_CHANGE_UK", "NET_LENDING_DWELLINGS_MO"], "value": [4.0, 1.0, 100], "unit": ["%", "%", "GBP Millions"], "frequency": ["Monthly"] * 3}).to_sql("economic_series", conn, index=False)
        response = build_housing_credit_response(conn); conn.close()
        self.assertEqual([chart.id for chart in response.charts], ["HC1", "HC2", "HC3", "HC4"])
        self.assertEqual(response.charts[1].baseline_date, "2024-01-31")
        self.assertEqual(response.charts[2].geography, "England and Wales")


if __name__ == "__main__": unittest.main()
