import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.validation.validate_warehouse import (
    REQUIRED_METRICS,
    REQUIRED_TABLES,
    WarehouseValidationError,
    validate_warehouse,
)


class WarehouseValidationTests(unittest.TestCase):
    def test_missing_database_fails_clearly(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.db"
            with self.assertRaisesRegex(WarehouseValidationError, "does not exist"):
                validate_warehouse(missing)

    def test_missing_required_tables_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.db"
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TABLE economic_series (metric_id TEXT)")
                connection.execute("INSERT INTO economic_series VALUES ('GDP_QOQ')")
                connection.commit()
            finally:
                connection.close()
            with self.assertRaisesRegex(WarehouseValidationError, "Required tables are missing"):
                validate_warehouse(path, validate_page_services=False)

    def test_complete_structural_fixture_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.db"
            connection = sqlite3.connect(path)
            try:
                connection.execute(
                    "CREATE TABLE economic_series (metric_id TEXT, value REAL)"
                )
                connection.executemany(
                    "INSERT INTO economic_series VALUES (?, 1.0)",
                    [(metric,) for metric in REQUIRED_METRICS],
                )
                for table in REQUIRED_TABLES - {"economic_series"}:
                    connection.execute(f'CREATE TABLE "{table}" (value REAL)')
                    connection.execute(f'INSERT INTO "{table}" VALUES (1.0)')
                connection.commit()
            finally:
                connection.close()

            summary = validate_warehouse(path, validate_page_services=False)

            self.assertEqual(summary["tables"], len(REQUIRED_TABLES))
            self.assertEqual(summary["core_metrics"], len(REQUIRED_METRICS))


if __name__ == "__main__":
    unittest.main()
