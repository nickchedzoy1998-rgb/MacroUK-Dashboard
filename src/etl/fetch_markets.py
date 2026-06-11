import yfinance as yf
import pandas as pd
from pathlib import Path
import sqlite3

from src.utilities.config_loader import load_config

# Helpers
y_config = load_config('metric_manifest', 'y_finance_metrics')
database = load_config('settings', 'databases', 'economics_db')

def extract(m: str, m_config: dict):
    "Returns Dataframe for a metrics datapoints"
    "Pass in a single dict from the config into the function in main"
    ticker = yf.Ticker(m_config.get('ticker', None))

    period = m_config.get('period', 'max')

    history = ticker.history(period=period)

    if history.empty:
        return 
    
    return history

def transform(m, m_config, df):
    "Takes a Dataframe converts to long form df for a single metrics data"
    df = df.reset_index()

    cols_all = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    cols = [col for col in cols_all if col in df.columns]

    df = df[cols]

    df[cols[1:]] = df[cols[1:]].apply(pd.to_numeric, errors='coerce')

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

    cols_rename = {col: col.lower() for col in cols}
    lower_cols = [col.lower() for col in cols]

    df = df.rename(columns=cols_rename)

    metric_dfs = []

    for col in lower_cols[1:]:
        split_df = df.copy()

        split_df = split_df[['date', col]]
        split_df = split_df.dropna(subset=col)

        split_df['metric_id'] = f'{m}_{col}'
        split_df['metric_name'] = m_config.get('name')
        split_df['value'] = split_df[col]
        split_df['unit'] = m_config.get('unit')
        split_df['source'] = 'YAHOO_FINANCE'
        split_df['frequency'] = m_config.get('frequency')

        split_df = split_df[['date', 'metric_id', 'metric_name', 'value', 'unit', 'source', 'frequency']]

        if not split_df.empty:
            metric_dfs.append(split_df)
    
    if not metric_dfs:
        return []
    
    combined_metric_df = pd.concat(metric_dfs, ignore_index=True)

    return combined_metric_df


def combine():
    "Combines all Metric DFs to one Dataframe"

    print('Initialising Yahoo Data Storage')
    yfin_dataframes = []

    for m, m_config in y_config.items():
        print(f'Extracting Data for {m}')

        extracted_history = extract(m=m, m_config=m_config)
        if not extracted_history.empty:
            print(f'Data successfully extracted for {m}')
            print('Starting Transformation...')

            combined_dataframe = transform(m=m, m_config=m_config, df=extracted_history)

            yfin_dataframes.append(combined_dataframe)
    
    if not yfin_dataframes:
        return 
    
    master_dataframe = pd.concat(yfin_dataframes, ignore_index=True)

    return master_dataframe


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


def load(master_df):
    """Combine the list of dataframes into one frame and write it to SQLite.
    This implementation avoids duplicate inserts by deduplicating the incoming
    data and using `INSERT OR IGNORE` against a target table with a primary key.
    """

    Path("data").mkdir(exist_ok=True)
    db_path = Path("data") / (database + ".db")

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
        print(f"Load failure: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    load(combine())
    # python -m src.etl.fetch_markets