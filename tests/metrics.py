import pandas as pd
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config

db = load_config('settings', 'databases', 'economics_db')
DB_PATH = Path("data") / f"{db}.db"

ons = list(load_config('metric_manifest', 'ons_metrics').keys())
boe = list(load_config('metric_manifest', 'boe_metrics').keys())
yahoo = list(load_config('metric_manifest', 'y_finance_metrics').keys())
hmlr = list(load_config('metric_manifest', 'hmlr_metrics').keys())
hmt = list(load_config('metric_manifest', 'hmt_metrics').keys())

metric_lists = [ons, boe, yahoo, hmlr, hmt]

metrics = []

for m_list in metric_lists:
    metrics.extend(m_list)


conn = sqlite3.connect(DB_PATH)
table = 'economic_series'

df = pd.read_sql_query(f'SELECT DISTINCT(METRIC_NAME) FROM {table}', conn)

# table_metrics = list(df['metric_id'].unique())


if __name__ == '__main__':

    # for m in metrics:
    #     if m not in table_metrics:
    #         print(m)

    with pd.option_context(
        'display.max_rows', None, 
        'display.max_columns', None,
        'display.max_colwidth', None
    ):
        print(df)

    conn.close()


# python -m tests.metrics