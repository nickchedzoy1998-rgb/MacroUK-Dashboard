import sqlite3
import unittest
from pathlib import Path

from src.api.services.page_data import (
    get_financial_markets_page,
    get_global_flows_page,
    get_home_page,
    get_housing_credit_page,
    get_macro_pulse_page,
    get_monetary_policy_page,
)
from src.api.dashboard.data_loader import load_home_data
from src.database.database_manager import configured_database_path


ROOT = Path(__file__).resolve().parents[1]


class DeploymentArchitectureTests(unittest.TestCase):
    def test_all_page_services_work_directly_without_fastapi(self):
        database_path = configured_database_path()
        builders = (
            get_home_page,
            get_macro_pulse_page,
            get_monetary_policy_page,
            get_housing_credit_page,
            get_financial_markets_page,
            get_global_flows_page,
        )
        for builder in builders:
            response = builder(database_path=database_path)
            self.assertTrue(response.model_dump(mode="json"))

    def test_dashboard_pages_have_no_local_http_dependency(self):
        pages = ROOT / "src" / "api" / "dashboard" / "pages"
        for path in pages.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("fetch_json", source, path.name)
            self.assertNotIn("build_chart_endpoint", source, path.name)
            self.assertNotIn("127.0.0.1", source, path.name)

    def test_streamlit_loader_returns_page_data_without_http(self):
        load_home_data.clear()
        response = load_home_data()
        self.assertEqual(response["kpis"][0]["kpi_id"], "GDP_GROWTH")
        self.assertIn("summary", response)

    def test_github_workflow_gates_upload_after_build_validation_and_tests(self):
        workflow = (
            ROOT / ".github" / "workflows" / "build-warehouse.yml"
        ).read_text(encoding="utf-8")
        pipeline = workflow.index("python -m src.etl.pipeline_runner")
        validation = workflow.index("python -m src.validation.validate_warehouse")
        tests = workflow.index("python -m pytest -q")
        upload = workflow.index("Upload validated warehouse")
        self.assertLess(pipeline, validation)
        self.assertLess(validation, tests)
        self.assertLess(tests, upload)


if __name__ == "__main__":
    unittest.main()
