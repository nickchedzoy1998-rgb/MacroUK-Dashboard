import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.database.database_manager import (
    DatabaseUnavailableError,
    configured_database_path,
    download_database,
    ensure_database_available,
    open_readonly_connection,
)


def create_database(path: Path, marker: str = "original") -> bytes:
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE marker (value TEXT)")
        connection.execute("INSERT INTO marker VALUES (?)", (marker,))
        connection.commit()
    finally:
        connection.close()
    return path.read_bytes()


class FakeResponse:
    def __init__(self, content: bytes, *, status_error: Exception | None = None):
        self.content = content
        self.status_error = status_error

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def iter_content(self, chunk_size):
        del chunk_size
        yield self.content


class DatabaseManagerTests(unittest.TestCase):
    def test_environment_path_override(self):
        with unittest.mock.patch.dict(os.environ, {"MACROUK_DATABASE_PATH": "custom/data.db"}):
            self.assertEqual(configured_database_path(), Path("custom/data.db"))

    def test_valid_local_database_skips_download(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "warehouse.db"
            create_database(target)
            request_get = Mock()

            result = ensure_database_available(path=target, request_get=request_get)

            self.assertEqual(result, target)
            request_get.assert_not_called()

    def test_successful_download_atomically_replaces_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "warehouse.db"
            source = root / "source.db"
            create_database(target, "old")
            content = create_database(source, "new")

            download_database(
                "https://example.test/warehouse.db",
                target,
                request_get=lambda *args, **kwargs: FakeResponse(content),
            )

            connection = sqlite3.connect(target)
            try:
                self.assertEqual(connection.execute("SELECT value FROM marker").fetchone()[0], "new")
            finally:
                connection.close()
            self.assertFalse(target.with_suffix(".db.download").exists())

    def test_invalid_download_preserves_existing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "warehouse.db"
            original = create_database(target, "old")

            with self.assertRaises(DatabaseUnavailableError):
                download_database(
                    "https://example.test/broken.db",
                    target,
                    request_get=lambda *args, **kwargs: FakeResponse(b"not sqlite"),
                )

            self.assertEqual(target.read_bytes(), original)

    def test_readonly_connection_rejects_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "warehouse.db"
            create_database(target)
            connection = open_readonly_connection(target)
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute("INSERT INTO marker VALUES ('write')")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
