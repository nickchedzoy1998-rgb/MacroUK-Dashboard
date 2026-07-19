import sqlite3
import unittest

from src.api.services.global_flows_api import build_global_flows_response
from src.etl.prepare_datasets.global_flows import DB_PATH


class GlobalFlowsApiTests(unittest.TestCase):
    def test_response_order_units_and_price_labels(self):
        with sqlite3.connect(DB_PATH) as conn:
            response = build_global_flows_response(conn)
        self.assertEqual([chart.id for chart in response.charts], ["GF1", "GF2", "GF3"])
        self.assertEqual(response.charts[1].series_metadata[0].unit, "Index")
        self.assertIn("price proxy", response.charts[1].series_metadata[0].label)
        self.assertEqual(response.charts[2].series_metadata[0].metric, "COM_OIL_BRENT_close_normalised")


if __name__ == "__main__":
    unittest.main()
