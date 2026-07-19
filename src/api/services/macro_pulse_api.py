"""Assembly of the validated Macro Pulse page response."""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd

from src.analytics.chart_transforms import coverage_report
from src.api.schemas.macro_pulse import (
    ChartCoverage,
    ChartInsight,
    ChartRecord,
    ChartSeriesMetadata,
    MacroPulseChart,
    MacroPulseKPI,
    MacroPulsePageMetadata,
    MacroPulseResponse,
    MacroPulseSummary,
)
from src.api.services.macro_pulse import build_macro_pulse_insights, build_macro_pulse_summary
from src.etl.prepare_datasets.macro_pulse import prepare_macro_pulse_kpis
from src.utilities.config_loader import load_config


CHART_ORDER = ("EGM", "IB", "LBH")
TABLES = {chart_id: f"chart_macropulse_{chart_id.lower()}" for chart_id in CHART_ORDER}


class MacroPulseDataError(RuntimeError):
    """Raised when a required prepared Macro Pulse table cannot be loaded."""


def _load_prepared_table(conn: sqlite3.Connection, chart_id: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(
            f"SELECT * FROM {TABLES[chart_id]} ORDER BY date ASC",
            conn,
        )
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        raise MacroPulseDataError(f"Prepared table unavailable for {chart_id}") from exc


def _series_metadata(chart_id: str, config: dict[str, Any]) -> list[ChartSeriesMetadata]:
    metrics = list(config.get("metrics", []))
    optional_metrics = list(config.get("optional_metrics", []))
    labels = config.get("metric_labels", {})
    units = config.get("units", {})
    roles = {
        "EGM": {"GDP_QOQ": ("bar", "left"), "GDP_YOY": ("line", "left")},
        "IB": {"CPI": ("line", "left"), "CORE_CPI": ("line", "left"), "HOUSE_PRICE_GROWTH": ("line", "left")},
        "LBH": {"UNRATE": ("line", "left"), "EMPRATE": ("line", "left"), "WAGE_GROWTH": ("line", "right")},
    }
    all_metrics = metrics + optional_metrics
    return [
        ChartSeriesMetadata(
            metric=metric,
            label=labels.get(metric, metric),
            unit=units.get(metric, "%"),
            role=roles[chart_id].get(metric, ("line", "left"))[0],
            axis=roles[chart_id].get(metric, ("line", "left"))[1],
            display_order=index,
            optional=metric in optional_metrics,
        )
        for index, metric in enumerate(all_metrics, start=1)
    ]


def _coverage(dataframe: pd.DataFrame, metrics: list[str]) -> ChartCoverage:
    available_columns = [metric for metric in metrics if metric in dataframe.columns]
    if available_columns:
        long_frame = dataframe.melt(
            id_vars=["date"],
            value_vars=available_columns,
            var_name="metric_id",
            value_name="value",
        )
    else:
        long_frame = pd.DataFrame(columns=["date", "metric_id", "value"])
    report = coverage_report(long_frame, metrics)
    return ChartCoverage(
        requested_metrics=report["requested_metrics"],
        available_metrics=report["present_metrics"],
        missing_metrics=report["missing_metrics"],
        first_observation=report["first_valid_date"],
        latest_observation=report["latest_valid_date"],
        valid_observations=report["valid_observations"],
    )


def _records(dataframe: pd.DataFrame, metrics: list[str]) -> list[ChartRecord]:
    if dataframe.empty:
        return []
    records: list[ChartRecord] = []
    for _, row in dataframe.iterrows():
        parsed_date = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(parsed_date):
            continue
        values = {}
        for metric in metrics:
            value = row.get(metric)
            values[metric] = None if pd.isna(value) else float(value)
        records.append(ChartRecord(date=parsed_date.date(), values=values))
    return records


def _chart_response(
    chart_id: str,
    dataframe: pd.DataFrame,
    config: dict[str, Any],
    insight: dict[str, Any] | None,
) -> MacroPulseChart:
    metrics = list(config.get("metrics", []))
    optional_metrics = list(config.get("optional_metrics", []))
    all_metrics = metrics + optional_metrics
    chart_insight = ChartInsight(**insight) if insight else None
    return MacroPulseChart(
        id=chart_id,
        title=config["name"],
        description=config.get("description", ""),
        frequency=config.get("frequency", config.get("aggregation", "")),
        chart_type=config.get("chart_type", "line"),
        series_metadata=_series_metadata(chart_id, config),
        records=_records(dataframe, all_metrics),
        insight=chart_insight,
        coverage=_coverage(dataframe, all_metrics),
        target=float(config["target"]) if config.get("target") is not None else None,
        zero_reference=0.0 if chart_id == "EGM" else None,
    )


def build_macro_pulse_response(conn: sqlite3.Connection) -> MacroPulseResponse:
    """Load prepared tables and assemble the validated page response."""
    config = load_config("charts", "MacroPulse")
    datasets = {chart_id: _load_prepared_table(conn, chart_id) for chart_id in CHART_ORDER}
    kpi_rows = prepare_macro_pulse_kpis(conn)
    summary = build_macro_pulse_summary(kpi_rows, datasets["LBH"])
    insights = {item["chart_id"]: item for item in build_macro_pulse_insights(datasets)}

    kpis = [
        MacroPulseKPI(
            id=row["kpi_id"],
            metric=row["metric_id"],
            name=row["name"],
            value=row["value"],
            delta=row["delta"],
            description=row["description"],
            date=row["date"],
            main_unit=row["main_unit"],
            delta_unit=row["delta_unit"],
            comparison_label=row["comparison_label"],
            delta_direction=row["delta_direction"],
        )
        for row in kpi_rows
    ]
    charts = [
        _chart_response(chart_id, datasets[chart_id], config[chart_id], insights.get(chart_id))
        for chart_id in CHART_ORDER
    ]
    return MacroPulseResponse(
        page=MacroPulsePageMetadata(
            id="macro_pulse",
            title="Macro Pulse",
            description="Track UK growth, inflation and labour-market momentum.",
        ),
        summary=MacroPulseSummary(**summary),
        kpis=kpis,
        charts=charts,
    )
