import requests
import pandas as pd
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config

# Helpers
ons_url = load_config('endpoints', 'gov', 'inflation')
database = load_config('settings', 'databases', 'economics_db')


def extract(url):
    "Uses config loader, hits the API, returns JSON."
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise ConnectionError(f'Extract failure: {e}')
    
    
def transform(raw_json):
    "Takes months key from json & converts to pd df"

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


if __name__ == '__main__':
    extract_json = extract(ons_url)

    dataframe = transform(extract_json)

    if dataframe is None:
        print('No dataframe to save')
    
    else:
        load(dataframe)

    # python -m src.etl.fetch_ons
