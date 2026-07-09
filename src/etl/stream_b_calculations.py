import pandas as pd
from pathlib import Path
import sqlite3
from typing import Optional
from datetime import date
import numpy as np

from src.utilities.config_loader import load_config
from src.etl.db_utils import ensure_data_dir, get_connection, get_latest_date


# Helpers
database = load_config('settings', 'databases', 'economics_db')
DB_PATH = Path('data') / f"{database}.db"

metric_configs = ['ons_metrics', 'boe_metrics', 'y_finance_metrics', 'hmlr_metrics', 'hmt_metrics']

# Monthly Metric:
cpi = load_config('metric_manifest', 'ons_metrics', 'CPI')
# Daily Metric:
bank_rate_da = load_config('metric_manifest', 'boe_metrics', 'BANK_RATE_DA')
# Quarterly Metric:
gdp_q = load_config('metric_manifest', 'ons_metrics', 'GDP_QOQ')


def extract():
    conn = sqlite3.connect(DB_PATH)
    table = 'economic_series'

    metric_ids = []

    monthly_metric_count = 0
    daily_metric_count = 0
    quarterly_metric_count = 0

    for c in metric_configs:
        config = load_config('metric_manifest', c)

        keys = list(config.keys())

        for k in keys:
            frequency = config[k].get('frequency')

            if frequency == 'Monthly' and monthly_metric_count <1:
                metric_ids.append(k)
                monthly_metric_count += 1

            if frequency == 'Daily' and daily_metric_count <1:
                metric_ids.append(k)
                daily_metric_count += 1

            if frequency == 'Quarterly' and quarterly_metric_count <1:
                metric_ids.append(k)
                quarterly_metric_count += 1

    placeholders = ", ".join(["?"] * len(metric_ids))
    query = f"SELECT * FROM {table} WHERE METRIC_ID IN ({placeholders})"

    df = pd.read_sql_query(query, conn, params=metric_ids)

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    df_wide = df.pivot(
        index='date', 
        columns='metric_id', 
        values='value'
    ).reset_index()

    df_wide.columns.name = None
    df_wide.set_index('date', inplace=True)

    df_wide = df_wide.resample('ME').agg({
        'BANK_RATE_DA': 'mean',
        'GDP_QOQ': 'last',
        'CPI': 'first'
    })

    df_wide['GDP_QOQ'] = df_wide['GDP_QOQ'].ffill()

    return df_wide






if __name__ == '__main__':
    print(extract())
    # print(cpi)


# python -m src.etl.stream_b_calculations