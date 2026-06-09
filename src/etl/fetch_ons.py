"""Extract, transform, and load configured ONS metrics into SQLite."""

import pandas as pd
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config
from src.utilities.http_client import fetch_json
from src.utilities.build_url import build_ons

# Helpers
database = load_config('settings', 'databases', 'economics_db')
ons_config = load_config('metric_manifest', 'ons_metrics')

def get_period_key(frequency):
    """Map a configured frequency to the matching ONS JSON period key."""
    if frequency == "Monthly":
        return "months"
    if frequency == "Quarterly":
        return "quarters"
    if frequency == "Yearly":
        return "years"
    raise ValueError(f"Unsupported frequency: {frequency}")


def transform(raw_json, m, m_config):
    """Convert one raw ONS response into the standard economic series schema."""
    period_key = get_period_key(m_config["frequency"])
    periods = raw_json.get(period_key)

    if periods is not None:
        df = pd.DataFrame(periods)

        if period_key == 'months':
            df['date'] = pd.to_datetime(df['date'], format='%Y %b')
        elif period_key == 'quarters':
            try:
                df['date'] = pd.PeriodIndex(df['date'].str.replace(' ', '-'), freq='Q').to_timestamp()
            except Exception as e:
                print(e)
        elif period_key == 'years':
            try:
                df['date'] = pd.to_datetime(df['date'], format='%Y')
            except Exception as e:
                print(e)



        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['date'] = df['date'].dt.date
        df = df.dropna(subset=['value'])

        df['metric_id'] = m
        df['metric_name'] = m_config.get('name', None)
        df['unit'] = m_config.get('unit', None)
        df['source'] = 'ONS'
        df['frequency'] = m_config.get('frequency', None)

        df = df[['date', 'metric_id', 'metric_name', 'value', 'unit', 'source', 'frequency']]

        return df
    
    return None


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


def load(df):
    """Write a combined economic series dataframe to the configured SQLite database.

    This implementation avoids duplicate inserts for repeated pipeline runs.
    """
    if df is None or df.empty:
        print("No data to load.")
        return

    df = df.drop_duplicates(subset=['date', 'metric_id', 'source'])

    Path("data").mkdir(exist_ok=True)
    db_path = Path("data") / (database + ".db")

    conn = sqlite3.connect(db_path)

    try:
        _ensure_target_table(conn)
        df.to_sql("economic_series_tmp", con=conn, if_exists="replace", index=False)
        conn.execute(
            "INSERT OR IGNORE INTO economic_series (date, metric_id, metric_name, value, unit, source, frequency)"
            " SELECT date, metric_id, metric_name, value, unit, source, frequency FROM economic_series_tmp"
        )
        conn.execute("DROP TABLE IF EXISTS economic_series_tmp")
        conn.commit()

        print(f"Successfully loaded {len(df)} rows into SQLite.")

    except Exception as e:
        print(f"Load failure: {e}")
    finally:
        conn.close()


def main():
    """Fetch, transform, combine, and load all configured ONS metrics."""
    dataframes = []

    for m, m_config in ons_config.items():
        url = build_ons(m)
        raw_json = fetch_json(url)

        print(f'Transforming json: {m}')
        df = transform(raw_json, m, m_config)

        if df is not None:
            dataframes.append(df)
    
    if not dataframes:
        print("No dataframes to load.")
        return

    master_df = pd.concat(dataframes, ignore_index=True)

    load(master_df)



if __name__ == '__main__':
    main()
    # for m, m_config in ons_config.items():
    #     url = build_ons(m)
    #     print(url)
# python -m src.etl.fetch_ons