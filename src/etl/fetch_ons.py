import pandas as pd
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config
from src.utilities.http_client import extract
from src.utilities.build_url import build_ons

# Helpers
database = load_config('settings', 'databases', 'economics_db')


def transform(raw_json):
    months = raw_json.get('months', None)

    if months is not None:
        df = pd.DataFrame(months)

        df['date'] = pd.to_datetime(df['date'], format='%Y %b')
        df['value'] = pd.to_numeric(df['value'])

        df['metric_id'] = 'CPI'
        df['metric_name'] = 'Consumer Price Index'
        df['unit'] = '%'
        df['source'] = 'ONS'
        df['frequency'] = 'Monthly'

        df = df[['date', 'metric_id', 'metric_name', 'value', 'unit', 'source', 'frequency']]

        return df
    
    return None


def load(df):
    if df is None or df.empty:
        print("No data to load.")
        return

    Path("data").mkdir(exist_ok=True)
    db_path = Path("data") / (database + ".db")

    conn = sqlite3.connect(db_path)

    try:
        df.to_sql(
            "economic_series", con=conn, if_exists="replace", index=False
        )

        print(f"Successfully loaded {len(df)} rows into SQLite.")

    except Exception as e:
        print(f"Load failure: {e}")
    finally:
        conn.close()


def main():
    # Build List of metrics to iterate through
    ons_metrics = []




if __name__ == '__main__':
    print(load_config('metric_manifest', 'ons_metrics'))
    
