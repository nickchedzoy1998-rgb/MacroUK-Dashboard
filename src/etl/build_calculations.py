import pandas as pd
from pathlib import Path
import sqlite3
from typing import Optional
from datetime import date

from src.utilities.config_loader import load_config
from src.etl.db_utils import ensure_data_dir, get_connection, get_latest_date


#Helpers
database = load_config('settings', 'databases', 'economics_db')
DB_PATH = Path('data') / f"{database}.db"


def get_all_data():
    query = "SELECT * FROM economic_series"
    try:
        with get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df
        
    except(sqlite3.OperationalError, pd.errors.DatabaseError):
        return None

def macro_cols(df, config):
    cols = list(config.keys())

    return cols

    df = df
    


if __name__ == '__main__':
    config = load_config('calculations', 'monthly_macro')
    print(macro_cols('df', config))

# python -m src.etl.build_calculations

    




