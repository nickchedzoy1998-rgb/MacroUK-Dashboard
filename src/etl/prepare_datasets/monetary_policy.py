"""Prepare native-frequency Monetary Policy and Liquidity datasets."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.analytics.chart_transforms import coverage_report, prepare_time_series
from src.utilities.config_loader import load_config


DATABASE = load_config("settings", "databases", "economics_db")
DB_PATH = Path("data") / f"{DATABASE}.db"

MP1_REQUIRED = ("BANK_RATE_DA", "SONIA")
MP1_OPTIONAL = ("ETF_UK_GILT_close",)
MP2_REQUIRED = ("M4_GROWTH_MO", "NOTES_COINS_GROWTH_MO")
MP3_REQUIRED = ("CORP_OVERDRAFT_COST_MO", "NET_LENDING_CORP_MO")


def _load_series(conn: sqlite3.Connection, metrics: Sequence[str]) -> pd.DataFrame:
    placeholders = ", ".join("?" for _ in metrics)
    return pd.read_sql_query(
        f"""
        SELECT date, metric_id, value, unit, frequency
        FROM economic_series
        WHERE metric_id IN ({placeholders})
        ORDER BY date ASC, metric_id ASC
        """,
        conn,
        params=list(metrics),
    )


def _prepare_long(frame: pd.DataFrame, metrics: Sequence[str]) -> pd.DataFrame:
    available = set(frame["metric_id"].dropna()) if not frame.empty else set()
    missing = [metric for metric in metrics if metric not in available]
    if missing:
        raise ValueError(f"Missing required Monetary Policy metrics: {', '.join(missing)}")
    prepared = frame[frame["metric_id"].isin(metrics)].copy()
    prepared["value"] = pd.to_numeric(prepared["value"], errors="coerce")
    prepared = prepared.dropna(subset=["value"])
    return prepare_time_series(
        prepared,
        date_column="date",
        metric_column="metric_id",
        duplicate_policy="raise",
    )


def _wide(frame: pd.DataFrame, metrics: Sequence[str], *, chart_id: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["date", *metrics, "chart"])
    result = frame.pivot(index="date", columns="metric_id", values="value").reset_index()
    result.columns.name = None
    for metric in metrics:
        if metric not in result:
            result[metric] = pd.NA
    result["chart"] = chart_id
    return result[["date", *metrics, "chart"]].sort_values("date").reset_index(drop=True)


def prepare_mp1_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare daily policy/overnight rates and an optional ETF price proxy."""
    required = _prepare_long(frame, MP1_REQUIRED)
    optional = frame[frame["metric_id"].isin(MP1_OPTIONAL)].copy()
    if not optional.empty:
        optional["value"] = pd.to_numeric(optional["value"], errors="coerce")
        optional = optional.dropna(subset=["value"])
        optional = prepare_time_series(optional, date_column="date", metric_column="metric_id", duplicate_policy="raise")
    combined = pd.concat([required, optional], ignore_index=True)
    result = _wide(combined, (*MP1_REQUIRED, *MP1_OPTIONAL), chart_id="MP1")
    result["BANK_RATE_SONIA_SPREAD"] = result["BANK_RATE_DA"] - result["SONIA"]
    result.loc[result[["BANK_RATE_DA", "SONIA"]].isna().any(axis=1), "BANK_RATE_SONIA_SPREAD"] = pd.NA
    return result[["date", *MP1_REQUIRED, *MP1_OPTIONAL, "BANK_RATE_SONIA_SPREAD"]]


def prepare_mp2_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare monthly money-supply and notes/coin growth without filling gaps."""
    prepared = _prepare_long(frame, MP2_REQUIRED)
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce").dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    prepared = prepare_time_series(prepared, date_column="date", metric_column="metric_id", duplicate_policy="raise")
    return _wide(prepared, MP2_REQUIRED, chart_id="MP2")


def prepare_mp3_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare monthly corporate borrowing cost and lending growth."""
    prepared = _prepare_long(frame, MP3_REQUIRED)
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce").dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    prepared = prepare_time_series(prepared, date_column="date", metric_column="metric_id", duplicate_policy="raise")
    return _wide(prepared, MP3_REQUIRED, chart_id="MP3")


def monetary_policy_coverage(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    """Return coverage metadata for all Monetary Policy chart inputs."""
    frame = _load_series(conn, (*MP1_REQUIRED, *MP1_OPTIONAL, *MP2_REQUIRED, *MP3_REQUIRED))
    reports = {}
    for chart_id, metrics in {
        "MP1": (*MP1_REQUIRED, *MP1_OPTIONAL),
        "MP2": MP2_REQUIRED,
        "MP3": MP3_REQUIRED,
    }.items():
        available = frame[frame["metric_id"].isin(metrics)]
        reports[chart_id] = coverage_report(available, metrics)
    return reports


def prepare_monetary_policy_datasets(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    """Prepare all three Monetary Policy chart tables."""
    mp1 = _load_series(conn, (*MP1_REQUIRED, *MP1_OPTIONAL))
    mp2 = _load_series(conn, MP2_REQUIRED)
    mp3 = _load_series(conn, MP3_REQUIRED)
    return {
        "MP1": prepare_mp1_dataset(mp1),
        "MP2": prepare_mp2_dataset(mp2),
        "MP3": prepare_mp3_dataset(mp3),
    }


def _latest_rows(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    rows = frame[frame["metric_id"] == metric].copy()
    rows["date"] = pd.to_datetime(rows["date"], errors="coerce")
    rows["value"] = pd.to_numeric(rows["value"], errors="coerce")
    return rows.dropna(subset=["date", "value"]).sort_values("date")


def _kpi(metric_id: str, name: str, description: str, rows: pd.DataFrame, *, comparison_label: str, delta_direction: str | None = None, previous_distinct: bool = False) -> dict[str, object] | None:
    if rows.empty:
        return None
    latest = rows.iloc[-1]
    previous_rows = rows[rows["value"] != latest["value"]] if previous_distinct else rows.iloc[:-1]
    delta = None if previous_rows.empty else float(latest["value"] - previous_rows.iloc[-1]["value"])
    return {
        "kpi_id": metric_id,
        "metric_id": metric_id,
        "name": name,
        "value": float(latest["value"]),
        "delta": delta,
        "description": description,
        "date": latest["date"].date(),
        "main_unit": "%",
        "delta_unit": "pp",
        "comparison_label": comparison_label,
        "delta_direction": delta_direction,
    }


def prepare_monetary_policy_kpis(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """Prepare Bank Rate, SONIA, spread and M4 headline KPIs."""
    raw = _load_series(conn, (*MP1_REQUIRED, "M4_GROWTH_MO"))
    bank = _latest_rows(raw, "BANK_RATE_DA")
    sonia = _latest_rows(raw, "SONIA")
    m4 = _latest_rows(raw, "M4_GROWTH_MO")
    bank_kpi = _kpi("BANK_RATE", "Bank Rate", "Official Bank Rate for the UK.", bank, comparison_label="at last rate change", previous_distinct=True)
    sonia_kpi = _kpi("SONIA", "SONIA", "Sterling Overnight Index Average rate.", sonia, comparison_label="vs previous observation")
    m4_kpi = _kpi("M4_GROWTH_MO", "M4 Growth", "Annual growth in broad money supply.", m4, comparison_label="vs previous month")

    common = bank.merge(sonia, on="date", suffixes=("_bank", "_sonia"))
    common["value"] = common["value_bank"] - common["value_sonia"]
    spread_kpi = _kpi("BANK_RATE_SONIA_SPREAD", "Bank Rate–SONIA Spread", "Difference between Bank Rate and SONIA on common observations.", common, comparison_label="vs previous common observation")
    return [row for row in (bank_kpi, sonia_kpi, spread_kpi, m4_kpi) if row is not None]


def write_monetary_policy_datasets(datasets: dict[str, pd.DataFrame], *, db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        for chart_id, dataframe in datasets.items():
            dataframe.to_sql(f"chart_monetary_policy_{chart_id.lower()}", conn, if_exists="replace", index=False)


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        datasets = prepare_monetary_policy_datasets(conn)
        coverage = monetary_policy_coverage(conn)
    write_monetary_policy_datasets(datasets)
    for chart_id, report in coverage.items():
        print(f"{chart_id}: present={report['present_metrics']}; missing={report['missing_metrics']}")
    print("Prepared Monetary Policy datasets: " + ", ".join(sorted(datasets)))


if __name__ == "__main__":
    main()
