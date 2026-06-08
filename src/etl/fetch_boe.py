"""Extract, transform, and load configured BoE metrics into SQLite."""

import pandas as pd
import sqlite3
import requests
from datetime import datetime
import io

from src.utilities.config_loader import load_config

# Helpers
database = load_config('settings', 'databases', 'economics_db')
metric_config = load_config('metric_manifest', 'boe_metrics')


def extract():
    endpoint = load_config('endpoints', 'base', 'boe')
    now = datetime.now().strftime("%d/%b/%Y")

    codes_list = [i["series_code"] for k, i in metric_config.items()]
    series_codes_string = ",".join(codes_list)

    payload = {
    "Datefrom": "01/Jan/1989",
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
        print(f"An error occurred while fetching data from BoE: {e}")


def transform(content):
    df = pd.read_csv(io.BytesIO(content))

    dataframes = []
    
    for m, i in metric_config.items():
        metric_df = df['DATE', [m['series_code']]]

        metric_df[m['series_code']] = pd.to_numeric(df['value'])

        metric_df['metric_id'] = m
        metric_df['metric_name'] = m.get('name', None)
        metric_df['unit'] = m.get('unit', None)
        metric_df['source'] = 'BOE'
        metric_df['frequency'] = m.get('frequency', None)

        metric_df = metric_df.rename(columns={
            'DATE': 'date',
            m['series_code']: 'value'
        })

        metric_df['date'] = pd.to_datetime(metric_df['date'])

        metric_df = metric_df[['date', 'metric_id', 'metric_name', 'value', 'unit', 'source', 'frequency']]

        dataframes.append(metric_df)


if __name__ == '__main__':
    print(extract())

    # python -m src.etl.fetch_boe
