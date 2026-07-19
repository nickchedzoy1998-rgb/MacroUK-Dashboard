import sqlite3
import unittest

import pandas as pd

from src.api.services.monetary_policy_api import build_monetary_policy_response


class MonetaryPolicyApiTests(unittest.TestCase):
    def test_response_order_and_price_metadata(self):
        conn = sqlite3.connect(":memory:")
        for table, data in {
            "chart_monetary_policy_mp1": pd.DataFrame({"date": ["2024-01-01"], "BANK_RATE_DA": [4.0], "SONIA": [3.9], "ETF_UK_GILT_close": [9.8], "BANK_RATE_SONIA_SPREAD": [0.1]}),
            "chart_monetary_policy_mp2": pd.DataFrame({"date": ["2024-01-31"], "M4_GROWTH_MO": [2.0], "NOTES_COINS_GROWTH_MO": [3.0]}),
            "chart_monetary_policy_mp3": pd.DataFrame({"date": ["2024-01-31"], "CORP_OVERDRAFT_COST_MO": [5.0], "NET_LENDING_CORP_MO": [-1.0]}),
        }.items(): data.to_sql(table, conn, index=False)
        pd.DataFrame({"date": ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-01", "2024-01-31"], "metric_id": ["BANK_RATE_DA", "SONIA", "M4_GROWTH_MO", "M4_GROWTH_MO", "M4_GROWTH_MO"], "value": [4.0, 3.9, 2.0, 2.1, 2.2], "unit": ["%", "%", "%", "%", "%"], "frequency": ["Daily", "Daily", "Monthly", "Monthly", "Monthly"]}).to_sql("economic_series", conn, index=False)
        response = build_monetary_policy_response(conn)
        conn.close()
        self.assertEqual([chart.id for chart in response.charts], ["MP1", "MP2", "MP3"])
        self.assertEqual(next(item for item in response.charts[0].series_metadata if item.metric == "ETF_UK_GILT_close").unit, "GBP price")
        self.assertNotIn("yield", next(item for item in response.charts[0].series_metadata if item.metric == "ETF_UK_GILT_close").label.lower())


if __name__ == "__main__":
    unittest.main()
