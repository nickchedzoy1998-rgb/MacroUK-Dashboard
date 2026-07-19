import sqlite3
import unittest

from src.api.services.financial_markets_api import build_financial_markets_response
from src.etl.prepare_datasets.financial_markets import DB_PATH


class FinancialMarketsApiTests(unittest.TestCase):
    def test_response_order_baseline_and_raw_hover_values(self):
        with sqlite3.connect(DB_PATH) as conn:
            response = build_financial_markets_response(conn)
        self.assertEqual([chart.id for chart in response.charts], ["FM1", "FM2", "FM3"])
        self.assertIsNotNone(response.charts[0].baseline_date)
        self.assertIn("FTSE_100_close", response.charts[0].records[-1].values)
        self.assertEqual(len(response.kpis), 4)


if __name__ == "__main__":
    unittest.main()
