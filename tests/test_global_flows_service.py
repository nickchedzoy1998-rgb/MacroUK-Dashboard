import unittest

from src.api.services.global_flows import build_global_flows_summary


class GlobalFlowsServiceTests(unittest.TestCase):
    def test_summary_keeps_asset_language_descriptive(self):
        summary = build_global_flows_summary([{"kpi_id": "STERLING_ERI", "value": 1.0}, {"kpi_id": "GBP_USD", "value": -0.4}, {"kpi_id": "BRENT", "value": -2.0}])
        self.assertIn("Sterling ERI", summary["headline"])
        self.assertIn("price proxies", summary["body"])
        self.assertIn("descriptive", summary["body"])


if __name__ == "__main__":
    unittest.main()
