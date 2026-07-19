"""Prepare Financial Markets and Equities chart datasets."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.analytics.chart_transforms import (
    coverage_report,
    normalise_to_common_baseline,
    prepare_time_series,
    resample_market_data_monthly,
    return_over_observations,
    year_to_date_return,
)
from src.utilities.config_loader import load_config


DATABASE = load_config("settings", "databases", "economics_db")
DB_PATH = Path("data") / f"{DATABASE}.db"

FM1_REQUIRED = ("FTSE_100_close", "FTSE_250_close", "FTSE_AIM_close")
FM2_HOUSEBUILDERS = ("EQ_TW_close", "EQ_BAR_close")
FM2_HPI = ("UK_HPI_INDEX_UK",)
FM3_REQUIRED = ("EQ_BARC_close", "EQ_BP_close", "EQ_RIO_close", "EQ_GSK_close", "SGE_L_close")


def _load(conn: sqlite3.Connection, metrics: Sequence[str]) -> pd.DataFrame:
    placeholders = ", ".join("?" for _ in metrics)
    return pd.read_sql_query(
        f"SELECT date, metric_id, value, unit, frequency FROM economic_series WHERE metric_id IN ({placeholders}) ORDER BY date ASC, metric_id ASC",
        conn,
        params=list(metrics),
    )


def _long(frame: pd.DataFrame, metrics: Sequence[str], *, monthly: bool = False) -> pd.DataFrame:
    present = set(frame.get("metric_id", []))
    missing = [metric for metric in metrics if metric not in present]
    if missing:
        raise ValueError(f"Missing required Financial Markets metrics: {', '.join(missing)}")
    result = frame[frame["metric_id"].isin(metrics)].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    if monthly:
        result["date"] = result["date"].dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    return prepare_time_series(
        result.dropna(subset=["date", "value"]),
        date_column="date",
        metric_column="metric_id",
        duplicate_policy="raise",
    )


def _wide(frame: pd.DataFrame, metrics: Sequence[str], chart: str) -> pd.DataFrame:
    result = frame.pivot(index="date", columns="metric_id", values="value").reset_index()
    result.columns.name = None
    for metric in metrics:
        if metric not in result:
            result[metric] = pd.NA
    result["chart"] = chart
    return result[["date", *metrics, "chart"]].sort_values("date").reset_index(drop=True)


def _append_returns(result: pd.DataFrame, source: pd.DataFrame, metrics: Sequence[str]) -> pd.DataFrame:
    for observations, suffix in ((21, "return_21d"), (63, "return_63d")):
        returns = return_over_observations(source, observations)
        values = returns.pivot(index="date", columns="metric_id", values="return_pct").add_suffix(f"_{suffix}")
        result = result.merge(values, left_on="date", right_index=True, how="left")
    ytd = year_to_date_return(source)
    values = ytd.pivot(index="date", columns="metric_id", values="return_pct").add_suffix("_return_ytd")
    result = result.merge(values, left_on="date", right_index=True, how="left")
    return result


def prepare_fm1_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    raw = _long(frame, FM1_REQUIRED)
    result = _wide(raw, FM1_REQUIRED, "FM1")
    normalised, baseline = normalise_to_common_baseline(raw, metrics=FM1_REQUIRED)
    if baseline is None:
        raise ValueError("No common valid baseline exists for UK equity indices")
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").add_suffix("_normalised")
    result = result.merge(rebased, left_on="date", right_index=True, how="left")
    result = _append_returns(result, raw, FM1_REQUIRED)
    result["baseline_date"] = baseline
    return result


def prepare_fm2_daily_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    return _wide(_long(frame, FM2_HOUSEBUILDERS), FM2_HOUSEBUILDERS, "FM2_DAILY")


def prepare_fm2_monthly_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    housebuilders = resample_market_data_monthly(_long(frame, FM2_HOUSEBUILDERS))
    hpi = _long(frame, FM2_HPI, monthly=True)
    monthly = pd.concat([housebuilders, hpi], ignore_index=True)
    raw = _wide(monthly, (*FM2_HOUSEBUILDERS, *FM2_HPI), "FM2_MONTHLY")
    normalised, baseline = normalise_to_common_baseline(monthly, metrics=(*FM2_HOUSEBUILDERS, *FM2_HPI))
    if baseline is None:
        raise ValueError("No common valid baseline exists for housebuilders and UK HPI")
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").add_suffix("_normalised")
    result = raw.merge(rebased, left_on="date", right_index=True, how="left")
    result["baseline_date"] = baseline
    return result


def prepare_fm3_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    raw = _long(frame, FM3_REQUIRED)
    result = _wide(raw, FM3_REQUIRED, "FM3")
    normalised, baseline = normalise_to_common_baseline(raw, metrics=FM3_REQUIRED)
    if baseline is None:
        raise ValueError("No common valid baseline exists for company proxies")
    rebased = normalised.pivot(index="date", columns="metric_id", values="normalised_value").add_suffix("_normalised")
    result = result.merge(rebased, left_on="date", right_index=True, how="left")
    result = _append_returns(result, raw, FM3_REQUIRED)
    result["baseline_date"] = baseline
    return result


def financial_markets_coverage(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    reports = {
        "FM1": coverage_report(_load(conn, FM1_REQUIRED), FM1_REQUIRED),
        "FM2": coverage_report(_load(conn, (*FM2_HOUSEBUILDERS, *FM2_HPI)), (*FM2_HOUSEBUILDERS, *FM2_HPI)),
        "FM3": coverage_report(_load(conn, FM3_REQUIRED), FM3_REQUIRED),
    }
    return reports


def prepare_financial_markets_datasets(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    return {
        "FM1": prepare_fm1_dataset(_load(conn, FM1_REQUIRED)),
        "FM2_DAILY": prepare_fm2_daily_dataset(_load(conn, FM2_HOUSEBUILDERS)),
        "FM2_MONTHLY": prepare_fm2_monthly_dataset(_load(conn, (*FM2_HOUSEBUILDERS, *FM2_HPI))),
        "FM3": prepare_fm3_dataset(_load(conn, FM3_REQUIRED)),
    }


def _rows(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    result = frame[frame.metric_id == metric].copy()
    result["date"] = pd.to_datetime(result.date, errors="coerce")
    result["value"] = pd.to_numeric(result.value, errors="coerce")
    return result.dropna(subset=["date", "value"]).sort_values("date")


def _return_kpi(kpi_id: str, name: str, metric: str, rows: pd.DataFrame, description: str) -> dict[str, object] | None:
    if rows.empty:
        return None
    calculated = return_over_observations(rows.rename(columns={"metric_id": "metric_id"}), 21)
    valid = calculated.dropna(subset=["return_pct"])
    if valid.empty:
        return None
    latest = valid.iloc[-1]
    return {
        "kpi_id": kpi_id,
        "metric_id": metric,
        "name": name,
        "value": float(latest["return_pct"]),
        "delta": None,
        "description": description,
        "date": pd.Timestamp(latest["date"]).date(),
        "main_unit": "%",
        "delta_unit": "%",
        "comparison_label": "over 1 month",
        "delta_direction": None,
    }


def prepare_financial_markets_kpis(conn: sqlite3.Connection) -> list[dict[str, object]]:
    raw = _load(conn, FM1_REQUIRED)
    returns = {}
    for metric in FM1_REQUIRED:
        rows = _rows(raw, metric)
        calculated = return_over_observations(rows, 21)
        valid = calculated.dropna(subset=["return_pct"])
        if not valid.empty:
            returns[metric] = valid.iloc[-1]
    names = {"FTSE_100_close": "FTSE 100", "FTSE_250_close": "FTSE 250", "FTSE_AIM_close": "FTSE AIM"}
    result = []
    for metric in FM1_REQUIRED:
        if metric not in returns:
            continue
        row = returns[metric]
        result.append({
            "kpi_id": metric.replace("_close", ""), "metric_id": metric, "name": names[metric],
            "value": float(row["return_pct"]), "delta": None,
            "description": f"One-month return for the {names[metric]} index.",
            "date": pd.Timestamp(row["date"]).date(), "main_unit": "%", "delta_unit": "%",
            "comparison_label": "over 1 month", "delta_direction": None,
        })
    if all(metric in returns for metric in ("FTSE_100_close", "FTSE_250_close")):
        first = returns["FTSE_250_close"]; second = returns["FTSE_100_close"]
        result.append({
            "kpi_id": "FTSE_250_RELATIVE", "metric_id": "FTSE_250_close_vs_FTSE_100_close",
            "name": "FTSE 250 relative performance", "value": float(first["return_pct"] - second["return_pct"]),
            "delta": None, "description": "FTSE 250 one-month return relative to the FTSE 100.",
            "date": max(pd.Timestamp(first.date), pd.Timestamp(second.date)).date(), "main_unit": "%", "delta_unit": "%",
            "comparison_label": "FTSE 250 minus FTSE 100", "delta_direction": None,
        })
    return result


def write_financial_markets_datasets(datasets: dict[str, pd.DataFrame], *, db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        for chart, dataframe in datasets.items():
            dataframe.to_sql(f"chart_financial_markets_{chart.lower()}", conn, if_exists="replace", index=False)


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        datasets = prepare_financial_markets_datasets(conn)
        coverage = financial_markets_coverage(conn)
    write_financial_markets_datasets(datasets)
    for chart, report in coverage.items():
        print(f"{chart}: present={report['present_metrics']}; missing={report['missing_metrics']}")
    print("Prepared Financial Markets datasets: " + ", ".join(sorted(datasets)))


if __name__ == "__main__":
    main()
