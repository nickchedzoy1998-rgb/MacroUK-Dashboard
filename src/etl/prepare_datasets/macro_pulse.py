"""Prepare native-frequency, chart-oriented Macro Pulse datasets."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.analytics.chart_transforms import coverage_report, prepare_time_series
from src.utilities.config_loader import load_config
from src.database.database_manager import configured_database_path


DATABASE = load_config("settings", "databases", "economics_db")
DB_PATH = configured_database_path()

GROWTH_REQUIRED = ("GDP_QOQ", "GDP_YOY")
INFLATION_REQUIRED = ("CPI", "CORE_CPI")
INFLATION_OPTIONAL = ("HOUSE_PRICE_GROWTH",)
LABOUR_REQUIRED = ("UNRATE", "EMPRATE", "WAGE_GROWTH")


def _load_series(conn: sqlite3.Connection, metrics: Sequence[str]) -> pd.DataFrame:
    if not metrics:
        return pd.DataFrame(columns=["date", "metric_id", "value", "frequency"])
    placeholders = ", ".join("?" for _ in metrics)
    return pd.read_sql_query(
        f"""
        SELECT date, metric_id, value, frequency
        FROM economic_series
        WHERE metric_id IN ({placeholders})
        ORDER BY date ASC, metric_id ASC
        """,
        conn,
        params=list(metrics),
    )


def _normalise_dates(frame: pd.DataFrame, frequency: str) -> pd.DataFrame:
    result = frame.copy()
    parsed = pd.to_datetime(result["date"], errors="coerce")
    if frequency == "Quarterly":
        result["date"] = parsed.dt.to_period("Q").dt.to_timestamp(how="end").dt.normalize()
    elif frequency == "Yearly":
        result["date"] = parsed.dt.to_period("Y").dt.to_timestamp(how="end").dt.normalize()
    elif frequency == "Monthly":
        result["date"] = parsed.dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    else:
        raise ValueError(f"Unsupported Macro Pulse frequency: {frequency}")
    return result


def _prepare_wide_dataset(
    frame: pd.DataFrame,
    *,
    metrics: Sequence[str],
    frequencies: dict[str, str],
    chart_id: str,
    optional_metrics: Sequence[str] = (),
) -> pd.DataFrame:
    available = set(frame["metric_id"].dropna()) if not frame.empty else set()
    missing_required = [metric for metric in metrics if metric not in available]
    if missing_required:
        raise ValueError(f"Missing required Macro Pulse metrics for {chart_id}: {', '.join(missing_required)}")

    series_frames = []
    for metric in (*metrics, *optional_metrics):
        metric_frame = frame[frame["metric_id"] == metric].copy()
        if metric_frame.empty:
            continue
        metric_frame = _normalise_dates(metric_frame, frequencies[metric])
        metric_frame["value"] = pd.to_numeric(metric_frame["value"], errors="coerce")
        metric_frame = metric_frame.dropna(subset=["date", "value"])
        metric_frame = prepare_time_series(
            metric_frame,
            date_column="date",
            metric_column="metric_id",
            duplicate_policy="raise",
        )
        series_frames.append(metric_frame[["date", "metric_id", "value"]].rename(columns={"value": metric}))

    if not series_frames:
        return pd.DataFrame(columns=["date", *metrics, *optional_metrics, "chart"])

    result = series_frames[0]
    for series in series_frames[1:]:
        result = result.merge(series, on="date", how="outer")
    for metric in (*metrics, *optional_metrics):
        if metric not in result.columns:
            result[metric] = pd.NA
    result["chart"] = chart_id
    return result[["date", *metrics, *optional_metrics, "chart"]].sort_values("date").reset_index(drop=True)


def prepare_growth_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare GDP Q/Q and native-frequency GDP year-on-year observations."""
    return _prepare_wide_dataset(
        frame,
        metrics=GROWTH_REQUIRED,
        frequencies={"GDP_QOQ": "Quarterly", "GDP_YOY": "Yearly"},
        chart_id="EGM",
    )


def prepare_inflation_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare monthly CPI, core CPI and optional housing-cost inflation."""
    core = frame[frame["metric_id"] == "CORE_CPI"].copy()
    if not core.empty:
        core["date"] = pd.to_datetime(core["date"], errors="coerce").dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
        core["value"] = pd.to_numeric(core["value"], errors="coerce")
        core = core.dropna(subset=["date", "value"])
        core = prepare_time_series(
            core,
            date_column="date",
            metric_column="metric_id",
            duplicate_policy="raise",
        )
        baseline = core[["date", "value"]].copy()
        baseline["date"] = baseline["date"] + pd.DateOffset(years=1)
        baseline = baseline.rename(columns={"value": "baseline_value"})
        core = core.merge(baseline, on="date", how="left")
        core["value"] = ((core["value"] / core["baseline_value"]) - 1) * 100
        core.loc[core["baseline_value"].isna() | core["baseline_value"].eq(0), "value"] = pd.NA
        core = core.drop(columns="baseline_value")

    other_metrics = frame[frame["metric_id"] != "CORE_CPI"]
    frame = pd.concat([other_metrics, core], ignore_index=True)
    return _prepare_wide_dataset(
        frame,
        metrics=INFLATION_REQUIRED,
        optional_metrics=INFLATION_OPTIONAL,
        frequencies={
            "CPI": "Monthly",
            "CORE_CPI": "Monthly",
            "HOUSE_PRICE_GROWTH": "Monthly",
        },
        chart_id="IB",
    )


def prepare_labour_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare monthly unemployment, employment and wage-growth observations."""
    return _prepare_wide_dataset(
        frame,
        metrics=LABOUR_REQUIRED,
        frequencies={metric: "Monthly" for metric in LABOUR_REQUIRED},
        chart_id="LBH",
    )


def macro_pulse_coverage(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    """Return coverage for each chart, including optional inflation data."""
    datasets = prepare_macro_pulse_datasets(conn)

    def wide_to_long(dataframe: pd.DataFrame, metrics: Sequence[str]) -> pd.DataFrame:
        return dataframe.melt(
            id_vars=["date"],
            value_vars=[metric for metric in metrics if metric in dataframe.columns],
            var_name="metric_id",
            value_name="value",
        )

    return {
        "EGM": coverage_report(wide_to_long(datasets["EGM"], GROWTH_REQUIRED), GROWTH_REQUIRED),
        "IB": coverage_report(
            wide_to_long(datasets["IB"], (*INFLATION_REQUIRED, *INFLATION_OPTIONAL)),
            (*INFLATION_REQUIRED, *INFLATION_OPTIONAL),
        ),
        "LBH": coverage_report(wide_to_long(datasets["LBH"], LABOUR_REQUIRED), LABOUR_REQUIRED),
    }


def prepare_macro_pulse_datasets(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    """Prepare all Macro Pulse chart tables from the economic series table."""
    frame = _load_series(
        conn,
        (*GROWTH_REQUIRED, *INFLATION_REQUIRED, *INFLATION_OPTIONAL, *LABOUR_REQUIRED),
    )
    return {
        "EGM": prepare_growth_dataset(frame[frame["metric_id"].isin(GROWTH_REQUIRED)]),
        "IB": prepare_inflation_dataset(
            frame[frame["metric_id"].isin((*INFLATION_REQUIRED, *INFLATION_OPTIONAL))]
        ),
        "LBH": prepare_labour_dataset(frame[frame["metric_id"].isin(LABOUR_REQUIRED)]),
    }


def _macro_pulse_kpi_config() -> dict[str, dict[str, object]]:
    home_config = load_config("charts", "Home")
    return {
        "GDP_GROWTH": {
            **home_config["GDP_GROWTH"],
            "metric": "GDP_QOQ",
            "comparison_type": "previous_observation",
            "comparison_label": "vs previous quarter",
        },
        "INFLATION": dict(home_config["INFLATION"]),
        "UNEMPLOYMENT": dict(home_config["UNEMPLOYMENT"]),
        "WAGE_GROWTH": {
            "name": "Wage Growth",
            "metric": "WAGE_GROWTH",
            "comparison_type": "previous_observation",
            "comparison_label": "vs previous month",
            "main_unit": "%",
            "delta_unit": "pp",
            "description": "Annual change in average weekly earnings.",
        },
    }


def prepare_macro_pulse_kpis(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """Prepare config-driven Macro Pulse headline KPI records."""
    config = _macro_pulse_kpi_config()
    metric_ids = [item["metric"] for item in config.values()]
    frame = _load_series(conn, metric_ids)
    rows: list[dict[str, object]] = []

    for kpi_id, kpi_config in config.items():
        metric_id = str(kpi_config["metric"])
        metric_frame = frame[frame["metric_id"] == metric_id].copy()
        metric_frame["value"] = pd.to_numeric(metric_frame["value"], errors="coerce")
        metric_frame["date"] = pd.to_datetime(metric_frame["date"], errors="coerce")
        metric_frame = metric_frame.dropna(subset=["date", "value"]).sort_values("date")
        if metric_frame.empty:
            continue

        latest = metric_frame.iloc[-1]
        value = float(latest["value"])
        delta = None
        comparison_type = kpi_config.get("comparison_type")
        if comparison_type == "previous_observation" and len(metric_frame) >= 2:
            delta = value - float(metric_frame.iloc[-2]["value"])
        elif comparison_type == "target" and kpi_config.get("target") is not None:
            delta = value - float(kpi_config["target"])

        rows.append(
            {
                "kpi_id": kpi_id,
                "metric_id": metric_id,
                "name": kpi_config["name"],
                "value": value,
                "date": latest["date"].date(),
                "delta": delta,
                "comparison_label": kpi_config.get("comparison_label"),
                "main_unit": kpi_config.get("main_unit"),
                "delta_unit": kpi_config.get("delta_unit"),
                "description": kpi_config.get("description"),
                "delta_direction": kpi_config.get("delta_direction"),
            }
        )
    return rows


def write_macro_pulse_datasets(
    datasets: dict[str, pd.DataFrame],
    *,
    db_path: Path = DB_PATH,
) -> None:
    """Write prepared chart datasets using the existing SQLite table names."""
    with sqlite3.connect(db_path) as conn:
        for chart_id, dataframe in datasets.items():
            dataframe.to_sql(
                f"chart_macropulse_{chart_id.lower()}",
                conn,
                if_exists="replace",
                index=False,
            )


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        datasets = prepare_macro_pulse_datasets(conn)
        coverage = macro_pulse_coverage(conn)
    write_macro_pulse_datasets(datasets)

    for chart_id, report in coverage.items():
        missing = report["missing_metrics"]
        optional_note = f"; missing: {', '.join(missing)}" if missing else ""
        print(
            f"{chart_id}: {len(report['present_metrics'])} present, "
            f"{len(report['valid_observations'])} covered metrics{optional_note}"
        )
    print("Prepared Macro Pulse datasets: " + ", ".join(sorted(datasets)))


if __name__ == "__main__":
    main()
