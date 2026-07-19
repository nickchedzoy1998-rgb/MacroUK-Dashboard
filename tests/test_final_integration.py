import ast
import unittest
from pathlib import Path

from src.api.main import app
from src.utilities.config_loader import load_config


ROOT = Path(__file__).resolve().parents[1]


class FinalIntegrationTests(unittest.TestCase):
    def test_all_page_routes_are_registered(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/api/home/summary", paths)
        self.assertIn("/api/macropulse/summary", paths)
        self.assertIn("/api/monetary-policy/summary", paths)
        self.assertIn("/api/housing-credit/summary", paths)
        self.assertIn("/api/financial-markets/summary", paths)
        self.assertIn("/api/global-flows/summary", paths)

    def test_navigation_pages_exist_and_config_ids_are_unique(self):
        page_dir = ROOT / "src" / "api" / "dashboard" / "pages"
        for name in ("home.py", "macro_pulse.py", "monetary_policy.py", "housing_credit.py", "financial_markets.py", "global_flows.py"):
            self.assertTrue((page_dir / name).exists())
        config = load_config("charts")
        ids = []
        for section in ("MacroPulse", "MonetaryPolicy", "HousingCredit", "FinancialMarkets", "GlobalFlows"):
            self.assertIn(section, config)
            ids.extend(config[section])
        self.assertEqual(len(ids), len(set(ids)))

    def test_app_declares_all_page_paths(self):
        tree = ast.parse((ROOT / "src" / "api" / "dashboard" / "app.py").read_text(encoding="utf-8"))
        source = ast.unparse(tree)
        for path in ("pages/macro_pulse.py", "pages/monetary_policy.py", "pages/housing_credit.py", "pages/financial_markets.py", "pages/global_flows.py"):
            self.assertIn(path, source)


if __name__ == "__main__":
    unittest.main()
