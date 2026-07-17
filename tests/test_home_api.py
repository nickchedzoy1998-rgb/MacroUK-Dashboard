import unittest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas.home import HomeKPI, HomeSummaryResponse


class HomeApiTests(unittest.TestCase):
    def test_schema_imports(self):
        self.assertTrue(HomeKPI is not None)
        self.assertTrue(HomeSummaryResponse is not None)

    def test_home_summary_endpoint(self):
        client = TestClient(app)
        response = client.get('/api/home/summary')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('kpis', payload)
        self.assertEqual(len(payload['kpis']), 6)
        self.assertEqual(payload['kpis'][0]['kpi_id'], 'GDP_GROWTH')


if __name__ == '__main__':
    unittest.main()
