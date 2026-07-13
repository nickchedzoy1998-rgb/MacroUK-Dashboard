import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config


database = load_config('settings', 'databases', 'economics_db')
DB_PATH = Path('data') / f"{database}.db"

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()
