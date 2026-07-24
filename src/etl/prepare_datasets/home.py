import pandas as pd
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config
from src.database.database_manager import configured_database_path

# CONFIGS:
home_kpi_config = load_config('charts', 'Home')
database_config = load_config('settings', 'databases')

# HELPERS:
kpi_list = list(home_kpi_config.keys())
db_path = configured_database_path()
table_name = "kpi_cards"


def get_df(kpi, conn):
    metric_id = home_kpi_config[kpi]["metric"]

    df = pd.read_sql_query(
        """
        SELECT date, metric_id, value
        FROM economic_series
        WHERE metric_id = ?
        ORDER BY date ASC
        """,
        conn,
        params=[metric_id],
    )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df.dropna(subset=["date", "value"])


def get_kpi_dict(kpi, df):
    config = home_kpi_config[kpi]

    metric_id = config["metric"]
    comparison_type = config["comparison_type"]

    value = float(df["value"].iloc[-1])
    date = df["date"].iloc[-1]
    delta = None

    if comparison_type == "previous_observation":
        if len(df) >= 2:
            previous = float(df["value"].iloc[-2])
            delta = value - previous

    elif comparison_type == "not applicable":
        pass

    elif comparison_type == "target":
        delta = value - float(config['target'])

    elif comparison_type == "previous_distinct_value":
        different_values = df.loc[df["value"] != value, "value"]

        if not different_values.empty:
            previous_distinct = float(different_values.iloc[-1])
            delta = value - previous_distinct

    elif comparison_type == "return_21d":
        if len(df) >= 22:
            previous = float(df["value"].iloc[-22])
            delta = ((value / previous) - 1) * 100

    else:
        raise ValueError(
            f"Unknown comparison type '{comparison_type}' for KPI '{kpi}'"
        )

    return {
        "kpi_id": kpi,
        "metric_id": metric_id,
        "value": value,
        "delta": delta,
        "date": date,
    }


def main():
    conn = sqlite3.connect(db_path)

    print('Creating KPI Metrics...')
    rows = []

    try:
        for kpi in kpi_list:
            print(f'Creating {kpi}')

            dataframe = get_df(kpi, conn=conn)

            if dataframe.empty:
                raise ValueError(f"No data found for required Home KPI {kpi}")
            print('Successfully extracted dataframe')
            
            row = get_kpi_dict(kpi, dataframe)

            rows.append(row)

        print('Building KPI dataframe')
        kpi_df = pd.DataFrame(rows)
        if kpi_df.empty:
            raise ValueError("No Home KPIs were created")
        if len(kpi_df) != len(kpi_list):
            raise ValueError(
                f"Home KPI preparation produced {len(kpi_df)} of {len(kpi_list)} required rows"
            )
        
        print(kpi_df)

        print('Attempting to save KPIs to SQL')
        kpi_df.to_sql(table_name, conn, if_exists='replace', index=False)

        print(f'Saved {len(kpi_df)} rows to {table_name}')
        return kpi_df
    
    finally:
        conn.close()

if __name__ == '__main__':
    main()
# python -m src.etl.prepare_datasets.home
