import unittest

from src.api.dependencies import get_db_conn
from src.api.routers.home import get_home_summary
from src.api.schemas.home import HomeKPI, HomeSummaryResponse


class HomeApiTests(unittest.TestCase):
    def test_schema_imports(self):
        self.assertTrue(HomeKPI is not None)
        self.assertTrue(HomeSummaryResponse is not None)

    def test_home_summary_response(self):
        conn_gen = get_db_conn()
        db = next(conn_gen)

        try:
            payload = get_home_summary(db).model_dump()
        finally:
            try:
                next(conn_gen)
            except StopIteration:
                pass

        self.assertIn('kpis', payload)
        self.assertIn('summary', payload)
        self.assertIn('highlights', payload)
        self.assertEqual(len(payload['kpis']), 6)
        self.assertEqual(payload['kpis'][0]['kpi_id'], 'GDP_GROWTH')
        self.assertLessEqual(len(payload['highlights']), 3)


if __name__ == '__main__':
    unittest.main()
