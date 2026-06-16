"""Extract, transform, and load configured HM Land Registry metrics into SQLite."""

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from src.etl.db_utils import get_latest_date
from src.utilities.config_loader import load_config
from src.utilities.http_client import fetch_json


# Helpers
database = load_config("settings", "databases", "economics_db")
endpoint = load_config("endpoints", "base", "land_reg")
metric_config = load_config("metric_manifest", "hmlr_metrics")


def build_hmlr_url(year_month: str, region: str) -> str:
    """Build a UK HPI URL for one month and one HMLR region slug."""
    year, month = year_month.split("-")
    return endpoint.format(year=year, month=month, region=region)


def month_range(start: str = "1995-01", from_date: date | None = None) -> list[str]:
    """Return monthly period strings from the start month through the current month."""
    if from_date is not None:
        start_date = pd.to_datetime(from_date).normalize().replace(day=1)
    else:
        start_date = pd.to_datetime(f"{start}-01")

    current_month = pd.Timestamp.today().normalize().replace(day=1)

    if start_date > current_month:
        return []

    return [d.strftime("%Y-%m") for d in pd.date_range(start_date, current_month, freq="MS")]


def extract_month_region(year_month: str, region: str):
    """Fetch one HMLR UK HPI month/region JSON payload.

    Missing or unreleased months are skipped by returning None.
    """
    url = build_hmlr_url(year_month, region)

    try:
        return fetch_json(url)
    except Exception as e:
        print(f"Skipping HMLR {year_month} {region}: {e}")
        return None


def _first_result_item(raw_json):
    """Return the first result item from the HMLR linked-data response."""
    if not raw_json:
        return None

    result = raw_json.get("result", {})
    primary_topic = result.get("primaryTopic")

    if isinstance(primary_topic, dict):
        return primary_topic

    items = result.get("items", [])

    if not items:
        return None

    return items[0]


def transform(raw_json, metric_id: str, metric_details: dict, date):
    """Convert one configured HMLR metric value into the standard series schema."""
    item = _first_result_item(raw_json)

    if not item:
        return None

    field = metric_details.get("field")

    if field not in item:
        print(f"HMLR response missing field {field} for {metric_id} on {date}.")
        return None

    value = pd.to_numeric(pd.Series([item.get(field)]), errors="coerce").iloc[0]

    if pd.isna(value):
        return None

    return pd.DataFrame(
        [
            {
                "date": date,
                "metric_id": metric_id,
                "metric_name": metric_details.get("name"),
                "value": value,
                "unit": metric_details.get("unit"),
                "source": "HMLR",
                "frequency": metric_details.get("frequency"),
            }
        ]
    )


def combine():
    """Fetch and combine all configured HMLR metric data into one dataframe."""
    dataframes = []
    response_cache = {}
    regions = sorted({details["region"] for details in metric_config.values()})

    latest = get_latest_date(source='HMLR')
    if latest is not None:
        start_month = (pd.to_datetime(latest).normalize().replace(day=1) + pd.offsets.MonthBegin(1)).date()
    else:
        start_month = None

    months = month_range(from_date=start_month)
    if not months:
        print("HMLR ETL: no new months to fetch.")
        return None

    for year_month in months:
        date = pd.to_datetime(f"{year_month}-01").date()

        for region in regions:
            cache_key = (year_month, region)

            if cache_key not in response_cache:
                print(f"Extracting HMLR data for {year_month} {region}")
                response_cache[cache_key] = extract_month_region(year_month, region)

            raw_json = response_cache[cache_key]

            if raw_json is None:
                continue

            for metric_id, metric_details in metric_config.items():
                if metric_details.get("region") != region:
                    continue

                df = transform(raw_json, metric_id, metric_details, date)

                if df is not None and not df.empty:
                    dataframes.append(df)

    if not dataframes:
        return None

    return pd.concat(dataframes, ignore_index=True)


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
    """Write HMLR series data to the configured SQLite database."""
    if master_df is None or master_df.empty:
        print("No data to load.")
        return

    master_df = master_df.drop_duplicates(subset=["date", "metric_id", "source"])

    Path("data").mkdir(exist_ok=True)
    db_path = Path("data") / f"{database}.db"

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

        print(f"Successfully loaded {len(master_df)} HMLR rows into SQLite.")

    except Exception as e:
        print(f"Load failure: {e}")
    finally:
        conn.close()


def main():
    """Fetch, transform, combine, and load all configured HMLR metrics."""
    master_df = combine()
    load(master_df)


if __name__ == "__main__":
    main()
    # python -m src.etl.fetch_land_reg
