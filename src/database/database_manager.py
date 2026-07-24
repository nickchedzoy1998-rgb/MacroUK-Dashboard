"""Manage the local read-only warehouse used by the deployed dashboard."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import requests

from src.utilities.config_loader import load_config


DATABASE_URL_ENV = "MACROUK_DATABASE_URL"
DATABASE_PATH_ENV = "MACROUK_DATABASE_PATH"
FORCE_REFRESH_ENV = "MACROUK_FORCE_DATABASE_REFRESH"


class DatabaseUnavailableError(RuntimeError):
    """Raised when no valid local or downloadable warehouse is available."""


def _runtime_setting(name: str) -> Any | None:
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    try:
        import streamlit as st

        return st.secrets.get(name)
    except Exception:
        return None


def configured_database_path(path: str | Path | None = None) -> Path:
    """Return an explicit, environment, or repository-configured database path."""
    if path is not None:
        return Path(path)
    override = os.getenv(DATABASE_PATH_ENV)
    if override:
        return Path(str(override))
    database = load_config("settings", "databases", "economics_db")
    return Path("data") / f"{database}.db"


def _as_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def database_integrity_ok(path: str | Path) -> bool:
    """Return whether a non-empty SQLite file opens and passes integrity_check."""
    candidate = Path(path)
    if not candidate.is_file() or candidate.stat().st_size == 0:
        return False
    connection = None
    try:
        uri = f"file:{candidate.resolve().as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        row = connection.execute("PRAGMA integrity_check").fetchone()
        return bool(row and str(row[0]).lower() == "ok")
    except sqlite3.Error:
        return False
    finally:
        if connection is not None:
            connection.close()


def download_database(
    url: str,
    target_path: str | Path,
    *,
    request_get=requests.get,
) -> Path:
    """Download and atomically replace a warehouse after SQLite validation."""
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".download")

    try:
        with request_get(url, stream=True, timeout=(10, 120)) as response:
            response.raise_for_status()
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
        if not database_integrity_ok(temporary):
            raise DatabaseUnavailableError("Downloaded warehouse failed SQLite integrity validation.")
        temporary.replace(target)
        return target
    except (requests.RequestException, OSError, sqlite3.Error) as exc:
        raise DatabaseUnavailableError(f"Unable to download the warehouse: {exc}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def ensure_database_available(
    *,
    path: str | Path | None = None,
    url: str | None = None,
    force_refresh: bool | None = None,
    request_get=requests.get,
) -> Path:
    """Return a valid local warehouse, downloading it only when required."""
    target = configured_database_path(path)
    refresh = _as_bool(_runtime_setting(FORCE_REFRESH_ENV)) if force_refresh is None else force_refresh

    if not refresh and database_integrity_ok(target):
        return target

    remote_url = url or _runtime_setting(DATABASE_URL_ENV)
    if not remote_url:
        if target.exists():
            reason = f"Local warehouse is invalid: {target}"
        else:
            reason = f"Local warehouse does not exist: {target}"
        raise DatabaseUnavailableError(
            f"{reason}. Configure {DATABASE_URL_ENV} to download the latest warehouse."
        )
    return download_database(str(remote_url), target, request_get=request_get)


def open_readonly_connection(path: str | Path) -> sqlite3.Connection:
    """Open a centralised read-only SQLite connection for app/service reads."""
    candidate = Path(path)
    if not database_integrity_ok(candidate):
        raise DatabaseUnavailableError(f"Warehouse is missing or invalid: {candidate}")
    uri = f"file:{candidate.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection
