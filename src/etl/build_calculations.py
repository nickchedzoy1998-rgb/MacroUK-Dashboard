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
macro_monthly_config = load_config('calculations', 'monthly_macro')


def get_data(metrics: list, date_from=None):
    placeholders = ", ".join(["?"] * len(metrics))
    
    query = f"SELECT * FROM economic_series WHERE METRIC_ID IN ({placeholders})"
    params = list(metrics)
    
    if date_from is not None:
        query += " AND DATE > ?"
        params.append(date_from)

    try:
        with get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df
    except(sqlite3.OperationalError, pd.errors.DatabaseError) as e:
        return None


def macro_cols(config: dict, date_from=None):
    raw_df = get_data(list(config.keys()), date_from=date_from)
    if raw_df is None or raw_df.empty:
        return pd.DataFrame()
        
    raw_df['DATE'] = pd.to_datetime(raw_df['DATE'], errors='coerce')
    
    df_wide = raw_df.pivot_table(
        index=['DATE'], 
        columns='METRIC_ID', 
        values='VALUE',
        aggfunc='mean'
    ).sort_index()

    calculated_features = []

    for col in config.keys():
        if col not in df_wide.columns:
            continue
            
        s = df_wide[col]
        res = pd.DataFrame(index=df_wide.index)
        
        res[f'{col}_prev_val'] = s.shift(1)
        res[f'{col}_rolling_3m'] = s.rolling(window=3, min_periods=1).mean()
        res[f'{col}_rolling_12m'] = s.rolling(window=12, min_periods=1).mean()
        res[f'{col}_prev_val_12m'] = s.shift(12)
        
        res[f'{col}_yoy_change'] = s - res[f'{col}_prev_val_12m']
        res[f'{col}_yoy_pct_change'] = res[f'{col}_yoy_change'] / res[f'{col}_prev_val_12m']
        
        res[f'{col}_trend'] = np.where(
            res[f'{col}_rolling_3m'] > res[f'{col}_rolling_12m'], 'Rising',
            np.where(res[f'{col}_rolling_3m'] < res[f'{col}_rolling_12m'], 'Falling', 'Flat')
        )
        
        change_type = config.get(col, {}).get('change_type')
        if change_type in ['pp', 'points']:
            res[f'{col}_change_{change_type}'] = s - res[f'{col}_prev_val']
            res[f'{col}_yoy_change_{change_type}'] = s - res[f'{col}_prev_val_12m']
        elif change_type == 'pct':
            res[f'{col}_change_pct'] = (s - res[f'{col}_prev_val']) / res[f'{col}_prev_val']
            
        calculated_features.append(res)
        
    final_df = pd.concat([df_wide] + calculated_features, axis=1).reset_index()
    
    return final_df
    
    







    



    


if __name__ == '__main__':
    config = load_config('calculations', 'monthly_macro')
    print(macro_cols('df', config))

# python -m src.etl.build_calculations

    




