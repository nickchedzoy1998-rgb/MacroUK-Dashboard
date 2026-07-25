import sqlite3

from src.database.database_manager import configured_database_path, open_readonly_connection


DB_PATH = configured_database_path()

def get_db_conn():
    conn = open_readonly_connection(DB_PATH)

    try:
        yield conn
    finally:
        conn.close()
