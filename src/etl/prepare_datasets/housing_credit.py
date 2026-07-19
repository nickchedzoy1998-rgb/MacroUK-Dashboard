"""Prepare Housing Market and Consumer Credit datasets."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.analytics.chart_transforms import coverage_report, normalise_to_common_baseline, prepare_time_series
from src.utilities.config_loader import load_config


DATABASE = load_config("settings", "databases", "economics_db")
DB_PATH = Path("data") / f"{DATABASE}.db"
HC1_REQUIRED = ("MORTGAGE_2YR_75LTV_MO", "UK_HPI_YOY_CHANGE_UK")
HC2_REQUIRED = ("UK_HPI_AVG_PRICE_UK", "UK_HPI_AVG_PRICE_LONDON", "UK_HPI_AVG_PRICE_NW")
HC3_REQUIRED = ("UK_HPI_CASH_SALES_VOL", "UK_HPI_MORTGAGE_SALES_VOL")
HC4_REQUIRED = ("NET_LENDING_DWELLINGS_MO", "NET_CONSUMER_CREDIT_MO")


def _load(conn: sqlite3.Connection, metrics: Sequence[str]) -> pd.DataFrame:
    placeholders = ", ".join("?" for _ in metrics)
    return pd.read_sql_query(f"SELECT date, metric_id, value, unit, frequency FROM economic_series WHERE metric_id IN ({placeholders}) ORDER BY date ASC, metric_id ASC", conn, params=list(metrics))


def _long(frame: pd.DataFrame, metrics: Sequence[str]) -> pd.DataFrame:
    missing = [metric for metric in metrics if metric not in set(frame.get("metric_id", []))]
    if missing:
        raise ValueError(f"Missing required Housing metrics: {', '.join(missing)}")
    result = frame[frame["metric_id"].isin(metrics)].copy()
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    result = result.dropna(subset=["date", "value"])
    return prepare_time_series(result, date_column="date", metric_column="metric_id", duplicate_policy="raise")


def _wide(frame: pd.DataFrame, metrics: Sequence[str], chart_id: str) -> pd.DataFrame:
    result = frame.pivot(index="date", columns="metric_id", values="value").reset_index()
    result.columns.name = None
    for metric in metrics:
        if metric not in result:
            result[metric] = pd.NA
    result["chart"] = chart_id
    return result[["date", *metrics, "chart"]].sort_values("date").reset_index(drop=True)


def prepare_hc1_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    return _wide(_long(frame, HC1_REQUIRED), HC1_REQUIRED, "HC1")


def prepare_hc2_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    raw = _long(frame, HC2_REQUIRED)
    normalised, baseline_date = normalise_to_common_baseline(raw, metrics=HC2_REQUIRED)
    if baseline_date is None:
        raise ValueError("No common valid baseline exists for regional housing prices")
    original = raw.pivot(index="date", columns="metric_id", values="value").reset_index()
    original.columns.name = None
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").reset_index()
    rebased.columns.name = None
    result = original.merge(rebased, on="date", how="outer", suffixes=("", "_normalised")).sort_values("date")
    result["baseline_date"] = baseline_date
    result["chart"] = "HC2"
    return result.reset_index(drop=True)


def prepare_hc3_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    raw = _long(frame, HC3_REQUIRED)
    result = _wide(raw, HC3_REQUIRED, "HC3")
    result["EW_TOTAL_TRANSACTIONS"] = result[list(HC3_REQUIRED)].sum(axis=1, min_count=2)
    result["CASH_SHARE_PCT"] = (result["UK_HPI_CASH_SALES_VOL"] / result["EW_TOTAL_TRANSACTIONS"]) * 100
    result.loc[result["EW_TOTAL_TRANSACTIONS"].isna() | result["EW_TOTAL_TRANSACTIONS"].le(0), "CASH_SHARE_PCT"] = pd.NA
    return result


def prepare_hc4_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    return _wide(_long(frame, HC4_REQUIRED), HC4_REQUIRED, "HC4")


def housing_credit_coverage(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    mapping = {"HC1": HC1_REQUIRED, "HC2": HC2_REQUIRED, "HC3": HC3_REQUIRED, "HC4": HC4_REQUIRED}
    reports = {}
    for chart, metrics in mapping.items():
        reports[chart] = coverage_report(_load(conn, metrics), metrics)
    return reports


def prepare_housing_credit_datasets(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    return {
        "HC1": prepare_hc1_dataset(_load(conn, HC1_REQUIRED)),
        "HC2": prepare_hc2_dataset(_load(conn, HC2_REQUIRED)),
        "HC3": prepare_hc3_dataset(_load(conn, HC3_REQUIRED)),
        "HC4": prepare_hc4_dataset(_load(conn, HC4_REQUIRED)),
    }


def _rows(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    rows = frame[frame.metric_id == metric].copy()
    rows["date"] = pd.to_datetime(rows.date, errors="coerce")
    rows["value"] = pd.to_numeric(rows.value, errors="coerce")
    return rows.dropna(subset=["date", "value"]).sort_values("date")


def _kpi(kpi_id: str, name: str, metric: str, description: str, rows: pd.DataFrame, unit: str, delta_unit: str) -> dict[str, object] | None:
    if rows.empty:
        return None
    latest = rows.iloc[-1]
    delta = None if len(rows) < 2 else float(latest.value - rows.iloc[-2].value)
    return {"kpi_id": kpi_id, "metric_id": metric, "name": name, "value": float(latest["value"]), "delta": delta, "description": description, "date": pd.Timestamp(latest["date"]).date(), "main_unit": unit, "delta_unit": delta_unit, "comparison_label": "vs previous observation", "delta_direction": None}


def prepare_housing_credit_kpis(conn: sqlite3.Connection) -> list[dict[str, object]]:
    raw = _load(conn, (*HC1_REQUIRED, "UK_HPI_CASH_SALES_VOL", "UK_HPI_MORTGAGE_SALES_VOL", "NET_LENDING_DWELLINGS_MO"))
    kpis = [
        _kpi("MORTGAGE_RATE", "Two-year mortgage rate", "MORTGAGE_2YR_75LTV_MO", "Monthly average rate on a two-year fixed mortgage at 75% LTV.", _rows(raw, "MORTGAGE_2YR_75LTV_MO"), "%", "pp"),
        _kpi("HOUSE_PRICE_GROWTH", "UK house-price growth", "UK_HPI_YOY_CHANGE_UK", "Annual change in UK house prices.", _rows(raw, "UK_HPI_YOY_CHANGE_UK"), "%", "pp"),
    ]
    total = raw[raw.metric_id.isin(HC3_REQUIRED)].pivot_table(index="date", columns="metric_id", values="value", aggfunc="last").reset_index()
    if not total.empty:
        total["value"] = total[list(HC3_REQUIRED)].sum(axis=1, min_count=2)
        kpis.append(_kpi("EW_TRANSACTION_VOLUME", "E&W transaction volume", "EW_TOTAL_TRANSACTIONS", "Derived England-and-Wales cash and mortgage-financed transaction volume.", total.rename(columns={"value": "value"}).assign(metric_id="EW_TOTAL_TRANSACTIONS"), "Transactions", "Transactions"))
    kpis.append(_kpi("NET_SECURED_LENDING", "Net secured lending", "NET_LENDING_DWELLINGS_MO", "Net secured lending to individuals.", _rows(raw, "NET_LENDING_DWELLINGS_MO"), "GBP millions", "GBP millions"))
    return [kpi for kpi in kpis if kpi is not None]


def write_housing_credit_datasets(datasets: dict[str, pd.DataFrame], *, db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        for chart, dataframe in datasets.items():
            dataframe.to_sql(f"chart_housing_credit_{chart.lower()}", conn, if_exists="replace", index=False)


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        datasets = prepare_housing_credit_datasets(conn)
        coverage = housing_credit_coverage(conn)
    write_housing_credit_datasets(datasets)
    for chart, report in coverage.items(): print(f"{chart}: present={report['present_metrics']}; missing={report['missing_metrics']}")


if __name__ == "__main__":
    main()
