"""Assembly of the Monetary Policy page response."""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd

from src.analytics.chart_transforms import coverage_report
from src.api.schemas.monetary_policy import (
    ChartCoverage,
    ChartInsight,
    ChartRecord,
    ChartSeriesMetadata,
    MonetaryPolicyChart,
    MonetaryPolicyKPI,
    MonetaryPolicyPageMetadata,
    MonetaryPolicyResponse,
    MonetaryPolicySummary,
)
from src.api.services.monetary_policy import build_monetary_policy_insights, build_monetary_policy_summary
from src.etl.prepare_datasets.monetary_policy import prepare_monetary_policy_kpis
from src.utilities.config_loader import load_config, resolve_metric_label


CHART_ORDER = ("MP1", "MP2", "MP3")
TABLES = {chart: f"chart_monetary_policy_{chart.lower()}" for chart in CHART_ORDER}


class MonetaryPolicyDataError(RuntimeError):
    pass


def _load_table(conn: sqlite3.Connection, chart_id: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(f"SELECT * FROM {TABLES[chart_id]} ORDER BY date ASC", conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        raise MonetaryPolicyDataError(f"Prepared table unavailable for {chart_id}") from exc


def _coverage(frame: pd.DataFrame, metrics: list[str]) -> ChartCoverage:
    available = [metric for metric in metrics if metric in frame.columns]
    long_frame = frame.melt(id_vars=["date"], value_vars=available, var_name="metric_id", value_name="value") if available else pd.DataFrame(columns=["date", "metric_id", "value"])
    report = coverage_report(long_frame, metrics)
    return ChartCoverage(
        requested_metrics=report["requested_metrics"],
        available_metrics=report["present_metrics"],
        missing_metrics=report["missing_metrics"],
        first_observation=report["first_valid_date"],
        latest_observation=report["latest_valid_date"],
        valid_observations=report["valid_observations"],
    )


def _records(frame: pd.DataFrame, metrics: list[str]) -> list[ChartRecord]:
    records = []
    for _, row in frame.iterrows():
        date_value = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(date_value):
            continue
        records.append(ChartRecord(date=date_value.date(), values={metric: None if metric not in frame or pd.isna(row.get(metric)) else float(row.get(metric)) for metric in metrics}))
    return records


def build_monetary_policy_response(conn: sqlite3.Connection) -> MonetaryPolicyResponse:
    config = load_config("charts", "MonetaryPolicy")
    datasets = {chart: _load_table(conn, chart) for chart in CHART_ORDER}
    kpi_rows = prepare_monetary_policy_kpis(conn)
    summary = build_monetary_policy_summary(kpi_rows)
    insights = {item["chart_id"]: item for item in build_monetary_policy_insights(datasets)}
    charts = []
    for chart_id in CHART_ORDER:
        chart_config = config[chart_id]
        metrics = list(chart_config.get("metrics", []))
        optional = list(chart_config.get("optional_metrics", []))
        all_metrics = metrics + optional
        labels = chart_config.get("metric_labels", {})
        units = chart_config.get("units", {})
        roles = chart_config.get("roles", {})
        axes = chart_config.get("axes", {})
        metadata = [
            ChartSeriesMetadata(metric=metric, label=resolve_metric_label(metric, labels), unit=units.get(metric, "%"), role=roles.get(metric, "line"), axis=axes.get(metric, "left"), display_order=index, optional=metric in optional)
            for index, metric in enumerate(all_metrics, start=1)
        ]
        charts.append(
            MonetaryPolicyChart(
                id=chart_id,
                title=chart_config["name"],
                description=chart_config["description"],
                frequency=chart_config["frequency"],
                chart_type=chart_config["chart_type"],
                series_metadata=metadata,
                records=_records(datasets[chart_id], all_metrics),
                insight=ChartInsight(**insights[chart_id]) if chart_id in insights else None,
                coverage=_coverage(datasets[chart_id], all_metrics),
                zero_reference=0.0 if chart_id in {"MP2", "MP3"} else None,
            )
        )
    return MonetaryPolicyResponse(
        page=MonetaryPolicyPageMetadata(id="monetary_policy", title="Monetary Policy & Liquidity", description="Track Bank of England policy and financial conditions through rates, money and business credit."),
        summary=MonetaryPolicySummary(**summary),
        kpis=[MonetaryPolicyKPI(id=row["kpi_id"], metric=row["metric_id"], **{key: row[key] for key in ("name", "value", "delta", "description", "date", "main_unit", "delta_unit", "comparison_label", "delta_direction")}) for row in kpi_rows],
        charts=charts,
    )
