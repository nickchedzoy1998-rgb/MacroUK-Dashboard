# *** Chart 1.1: Economic Growth Momentum ***
# *** Chart 1.2: The Inflation Battle ***
# *** Chart 1.3: Labor Market Health ***

import pandas as pd
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config

# CONFIGS:
macropulse_config = load_config('charts', 'MacroPulse')
database_config = load_config('settings', 'databases')

# HELPERS:
charts_list = list(macropulse_config.keys())
metric_manifest_keys = ['ons_metrics', 'boe_metrics', 'y_finance_metrics', 'hmlr_metrics', 'hmt_metrics']
db_path = Path('data') / f"{database_config['economics_db']}.db"
conn = sqlite3.connect(db_path)

resample_map = {
    'Daily': 'mean',
    'Monthly': 'first',
    'Quarterly': 'last',
    'Yearly': 'first'
}

aggregation_map = {
    'Monthly': 'ME',
    'Quarterly': 'QE'
}

def frequency_map():
    frequency_map = {}

    for c in charts_list:
        metrics = macropulse_config[c]['metrics']

        for m in metrics:
            for manifest_key in metric_manifest_keys:

                manifest_config = load_config('metric_manifest', manifest_key)

                if manifest_config.get(m, None) == None:
                    continue

                else:
                    frequency = manifest_config[m].get('frequency')
                    frequency_map[m] = frequency
                    break
    
    return frequency_map


def extract_df(chart, f_map):
    metrics = macropulse_config[chart]['metrics']

    placeholders = ', '.join(['?'] * len(metrics))
    query = f"SELECT * FROM economic_series WHERE METRIC_ID IN ({placeholders})"

    df = pd.read_sql_query(query, conn, params=metrics)
    
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    df_wide = df.pivot(
        index='date', 
        columns='metric_id', 
        values='value'
    ).reset_index()

    df_wide.columns.name = None
    df_wide.set_index('date', inplace=True)

    aggregation_level = aggregation_map.get(macropulse_config[chart]['aggregation'])
    resample_dict = {m: resample_map[f_map[m]] for m in metrics}
    df_wide = df_wide.resample(aggregation_level).agg(resample_dict)

    for col in list(df_wide.columns):
        if f_map[col] != 'Quarterly':
            df_wide[col] = df_wide[col].ffill()

    df_clean = df_wide.dropna()
    df_clean['chart'] = chart
    df_clean.reset_index(inplace=True)

    return df_clean


def main():
    # Extract Frequency Map:
    f_map = frequency_map()
    if f_map:
        print('Frequency Map Created:')
        print(f_map)

    # Extract DF and for each chart and save to new table.
    for chart in charts_list:
        print(f'Extracting data for {chart}')

        df = extract_df(chart=chart, f_map=f_map)

        if not df.empty:
            print(f'Successfully Extracted dataframe for {chart}')
            print(f'Chart Metrics: {df.columns}')

        table_name = f"chart_macropulse_{chart.lower()}"
        print(f'Preparing to save {chart} as {table_name} in {db_path}')
        
        df.to_sql(name=table_name, con=conn, if_exists='replace', index=False)

    conn.close()


if __name__ == '__main__':
    main()


# python -m src.etl.prepare_datasets.macro_pulse