"""Prepare Currency, Commodities and Fixed Income datasets."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.analytics.chart_transforms import coverage_report, normalise_to_common_baseline, prepare_time_series, return_over_observations
from src.utilities.config_loader import load_config


DATABASE = load_config("settings", "databases", "economics_db")
DB_PATH = Path("data") / f"{DATABASE}.db"
GF1_REQUIRED = ("STERLING_ERI_MO", "USD_GBP_SPOT_MO", "EUR_GBP_SPOT_MO")
GF2_REQUIRED = ("ETF_UK_GILT_close", "COM_GOLD_close")
GF2_OPTIONAL = ("ETF_UK_TIPS_close",)
GF3_REQUIRED = ("COM_OIL_BRENT_close", "COM_OIL_WTI_close")


def _load(conn: sqlite3.Connection, metrics: Sequence[str]) -> pd.DataFrame:
    placeholders = ", ".join("?" for _ in metrics)
    return pd.read_sql_query(f"SELECT date, metric_id, value, unit, frequency FROM economic_series WHERE metric_id IN ({placeholders}) ORDER BY date ASC, metric_id ASC", conn, params=list(metrics))


def _long(frame: pd.DataFrame, metrics: Sequence[str], *, monthly: bool = False) -> pd.DataFrame:
    missing = [metric for metric in metrics if metric not in set(frame.get("metric_id", []))]
    if missing:
        raise ValueError(f"Missing required Global Flows metrics: {', '.join(missing)}")
    result = frame[frame["metric_id"].isin(metrics)].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    if monthly:
        result["date"] = result["date"].dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    return prepare_time_series(result.dropna(subset=["date", "value"]), date_column="date", metric_column="metric_id", duplicate_policy="raise")


def _wide(frame: pd.DataFrame, metrics: Sequence[str], chart: str) -> pd.DataFrame:
    result = frame.pivot(index="date", columns="metric_id", values="value").reset_index(); result.columns.name = None
    for metric in metrics:
        if metric not in result: result[metric] = pd.NA
    result["chart"] = chart
    return result[["date", *metrics, "chart"]].sort_values("date").reset_index(drop=True)


def _returns(result: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    for observations, suffix in ((21, "return_21d"), (63, "return_63d")):
        values = return_over_observations(source, observations).pivot(index="date", columns="metric_id", values="return_pct").add_suffix(f"_{suffix}")
        result = result.merge(values, left_on="date", right_index=True, how="left")
    return result


def prepare_gf1_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    source = _long(frame, GF1_REQUIRED, monthly=True)
    result = _wide(source, GF1_REQUIRED, "GF1")
    normalised, baseline = normalise_to_common_baseline(source, metrics=GF1_REQUIRED)
    if baseline is None: raise ValueError("No common monthly sterling baseline exists")
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").add_suffix("_normalised")
    result = result.merge(rebased, left_on="date", right_index=True, how="left")
    result["baseline_date"] = baseline
    result["STERLING_ERI_MO_return_1m"] = return_over_observations(source, 1).pivot(index="date", columns="metric_id", values="return_pct")["STERLING_ERI_MO"]
    return result


def prepare_gf2_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    source = _long(frame, GF2_REQUIRED)
    optional = frame[frame["metric_id"].isin(GF2_OPTIONAL)].copy()
    if not optional.empty:
        optional["date"] = pd.to_datetime(optional["date"], errors="coerce")
        optional["value"] = pd.to_numeric(optional["value"], errors="coerce")
        optional = prepare_time_series(optional.dropna(subset=["date", "value"]), date_column="date", metric_column="metric_id", duplicate_policy="raise")
        source = pd.concat([source, optional], ignore_index=True)
    all_metrics = (*GF2_REQUIRED, *GF2_OPTIONAL)
    result = _wide(source, all_metrics, "GF2")
    normalise_metrics = tuple(metric for metric in all_metrics if metric in set(source["metric_id"]))
    normalised, baseline = normalise_to_common_baseline(source, metrics=normalise_metrics)
    if baseline is None: raise ValueError("No common daily fixed-income and gold baseline exists")
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").add_suffix("_normalised")
    result = result.merge(rebased, left_on="date", right_index=True, how="left")
    result = _returns(result, source)
    result["baseline_date"] = baseline
    return result


def prepare_gf3_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    source = _long(frame, GF3_REQUIRED)
    result = _wide(source, GF3_REQUIRED, "GF3")
    normalised, baseline = normalise_to_common_baseline(source, metrics=GF3_REQUIRED)
    if baseline is None: raise ValueError("No common daily oil baseline exists")
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").add_suffix("_normalised")
    result = result.merge(rebased, left_on="date", right_index=True, how="left")
    result = _returns(result, source)
    result["BRENT_WTI_SPREAD"] = result["COM_OIL_BRENT_close"] - result["COM_OIL_WTI_close"]
    result["baseline_date"] = baseline
    return result


def global_flows_coverage(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    return {"GF1": coverage_report(_load(conn, GF1_REQUIRED), GF1_REQUIRED), "GF2": coverage_report(_load(conn, (*GF2_REQUIRED, *GF2_OPTIONAL)), (*GF2_REQUIRED, *GF2_OPTIONAL)), "GF3": coverage_report(_load(conn, GF3_REQUIRED), GF3_REQUIRED)}


def prepare_global_flows_datasets(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    return {"GF1": prepare_gf1_dataset(_load(conn, GF1_REQUIRED)), "GF2": prepare_gf2_dataset(_load(conn, (*GF2_REQUIRED, *GF2_OPTIONAL))), "GF3": prepare_gf3_dataset(_load(conn, GF3_REQUIRED))}


def _return_kpi(kpi_id: str, name: str, metric: str, source: pd.DataFrame, description: str, observations: int) -> dict[str, object] | None:
    rows = return_over_observations(_long(source, (metric,), monthly=observations == 1), observations).dropna(subset=["return_pct"])
    if rows.empty: return None
    row = rows.iloc[-1]
    return {"kpi_id": kpi_id, "metric_id": metric, "name": name, "value": float(row["return_pct"]), "delta": None, "description": description, "date": pd.Timestamp(row.date).date(), "main_unit": "%", "delta_unit": "%", "comparison_label": "over previous month" if observations == 1 else "over 1 month", "delta_direction": None}


def prepare_global_flows_kpis(conn: sqlite3.Connection) -> list[dict[str, object]]:
    monthly = _load(conn, GF1_REQUIRED)
    daily = _load(conn, (*GF2_REQUIRED, *GF3_REQUIRED))
    rows = [
        _return_kpi("STERLING_ERI", "Sterling ERI", "STERLING_ERI_MO", monthly, "Monthly change in the sterling effective exchange rate index.", 1),
        _return_kpi("GBP_USD", "GBP/USD", "USD_GBP_SPOT_MO", monthly, "Monthly change in the BoE USD per GBP spot rate.", 1),
        _return_kpi("UK_GILT_ETF", "UK gilt ETF", "ETF_UK_GILT_close", daily, "One-month return for a UK gilt ETF price proxy.", 21),
        _return_kpi("BRENT", "Brent crude", "COM_OIL_BRENT_close", daily, "One-month return in Brent crude, USD per barrel.", 21),
    ]
    return [row for row in rows if row is not None]


def write_global_flows_datasets(datasets: dict[str, pd.DataFrame], *, db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        for chart, dataframe in datasets.items(): dataframe.to_sql(f"chart_global_flows_{chart.lower()}", conn, if_exists="replace", index=False)


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        datasets = prepare_global_flows_datasets(conn); coverage = global_flows_coverage(conn)
    write_global_flows_datasets(datasets)
    for chart, report in coverage.items(): print(f"{chart}: present={report['present_metrics']}; missing={report['missing_metrics']}")


if __name__ == "__main__": main()
