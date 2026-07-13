import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from src.utilities.config_loader import load_config


database = load_config('settings', 'databases', 'economics_db')
DB_PATH = Path('data') / f"{database}.db"


def ensure_data_dir() -> None:
    Path('data').mkdir(exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    return sqlite3.connect(DB_PATH)


def get_latest_date(metric_id: Optional[str] = None, metric_id_pattern: Optional[str] = None, source: Optional[str] = None) -> Optional[date]:
    if metric_id is None and metric_id_pattern is None and source is None:
        raise ValueError('At least one of metric_id, metric_id_pattern, or source must be provided.')

    clauses = []
    params = []

    if metric_id is not None:
        clauses.append('metric_id = ?')
        params.append(metric_id)
    if metric_id_pattern is not None:
        clauses.append('metric_id LIKE ?')
        params.append(metric_id_pattern)
    if source is not None:
        clauses.append('source = ?')
        params.append(source)

    query = f"SELECT MAX(date) FROM economic_series WHERE {' AND '.join(clauses)}"

    try:
        with get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            latest = row[0] if row else None
            if latest is None:
                return None
            if isinstance(latest, str):
                return date.fromisoformat(latest)
            return latest
    except sqlite3.OperationalError:
        return None
