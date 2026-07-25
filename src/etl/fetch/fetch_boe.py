"""Extract, transform, and load configured Bank of England metrics into SQLite.

This module fetches BoE CSV data for configured series codes, normalises
it into a shared economic series schema, and writes the combined result
into the configured SQLite database.
"""

import pandas as pd
import sqlite3
import requests
from datetime import datetime, timedelta
import io
from pathlib import Path

from src.utilities.db_utils import get_latest_date
from src.utilities.config_loader import load_config
from src.database.database_manager import configured_database_path

# Helpers
database = load_config('settings', 'databases', 'economics_db')
metric_config = load_config('metric_manifest', 'boe_metrics')


def _get_extract_from_date() -> str | None:
    latest = get_latest_date(source='BOE')

    if latest is None:
        start_date = datetime(1989, 1, 1).date()
    else:
        start_date = latest + timedelta(days=1)

    today = datetime.now().date()
    if start_date > today:
        return None

    return start_date.strftime("%d/%b/%Y")


def extract():
    """Request BoE time series CSV data for all configured series codes.

    Returns:
        bytes: Raw CSV response content from the Bank of England.
        None: If the request fails.
    """
    endpoint = load_config('endpoints', 'base', 'boe')
    date_from = _get_extract_from_date()

    if date_from is None:
        print("BOE ETL: no new date range to fetch.")
        return None

    now = datetime.now().strftime("%d/%b/%Y")

    codes_list = [i["series_code"] for k, i in metric_config.items()]
    series_codes_string = ",".join(codes_list)

    payload = {
        "Datefrom": date_from,
        "Dateto": now,
        "SeriesCodes": series_codes_string,
        "CSVF": "TN",
        "UsingCodes": "Y",
        "VPD": "Y",
        "VFD": "N",
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
    }

    try:
        response = requests.get(endpoint, headers=headers, params=payload, timeout=15)
        response.raise_for_status()
        return response.content

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Bank of England extraction failed: {e}") from e


def transform(content):
    """Convert raw BoE CSV content into a list of normalized dataframes.

    Args:
        content (bytes): CSV bytes returned by :func:`extract`.

    Returns:
        list[pandas.DataFrame]: A dataframe per configured metric, each with
        standard columns [date, metric_id, metric_name, value, unit, source, frequency].
    """
    df = pd.read_csv(io.BytesIO(content))

    dataframes = []
    
    for m, i in metric_config.items():
        series_code = i['series_code']

        if series_code not in df.columns:
            print(f"BOE response missing series column: {series_code}")
            continue

        metric_df = df[['DATE', series_code]].copy()
        metric_df[series_code] = pd.to_numeric(metric_df[series_code], errors='coerce')

        metric_df['metric_id'] = m
        metric_df['metric_name'] = i.get('name', None)
        metric_df['unit'] = i.get('unit', None)
        metric_df['source'] = 'BOE'
        metric_df['frequency'] = i.get('frequency', None)

        metric_df = metric_df.rename(columns={
            'DATE': 'date',
            series_code: 'value'
        })

        metric_df['date'] = pd.to_datetime(metric_df['date'], errors='coerce').dt.date
        metric_df = metric_df.dropna(subset=['value'])

        metric_df = metric_df[['date', 'metric_id', 'metric_name', 'value', 'unit', 'source', 'frequency']]

        if metric_df.empty:
            continue

        dataframes.append(metric_df)
    
    return dataframes


def _ensure_target_table(conn):
    """Ensure the economic_series table exists with a uniqueness constraint."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS economic_series (
            date TEXT,
            metric_id TEXT,
            metric_name TEXT,
            value REAL,
            unit TEXT,
            source TEXT,
            frequency TEXT,
            PRIMARY KEY (date, metric_id, source)
        )
        """
    )


def load(dataframes: list):
    """Combine the list of dataframes into one frame and write it to SQLite.

    This implementation avoids duplicate inserts by deduplicating the incoming
    data and using `INSERT OR IGNORE` against a target table with a primary key.
    """
    if not dataframes:
        print("No data to load.")
        return

    master_df = pd.concat(dataframes, ignore_index=True)
    master_df = master_df.drop_duplicates(subset=['date', 'metric_id', 'source'])

    db_path = configured_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)

    try:
        _ensure_target_table(conn)
        master_df.to_sql("economic_series_tmp", con=conn, if_exists="replace", index=False)
        conn.execute(
            "INSERT OR IGNORE INTO economic_series (date, metric_id, metric_name, value, unit, source, frequency)"
            " SELECT date, metric_id, metric_name, value, unit, source, frequency FROM economic_series_tmp"
        )
        conn.execute("DROP TABLE IF EXISTS economic_series_tmp")
        conn.commit()

        print(f"Successfully loaded {len(master_df)} rows into SQLite.")

    except Exception as e:
        raise RuntimeError(f"Bank of England load failed: {e}") from e
    finally:
        conn.close()


def main():
    content = extract()

    if content is None:
        print("No data extracted from BoE.")
    else:
        dataframes = transform(content)
        load(dataframes)



if __name__ == '__main__':
    content = extract()

    if content is None:
        print("No data extracted from BoE.")
    else:
        dataframes = transform(content)
        load(dataframes)

    # python -m src.etl.fetch_boe
