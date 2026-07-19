"""Assembly of the Currency, Commodities and Fixed Income API response."""

from __future__ import annotations

import sqlite3

import pandas as pd

from src.analytics.chart_transforms import coverage_report
from src.api.schemas.global_flows import GlobalFlowsChart, GlobalFlowsKPI, GlobalFlowsPage, GlobalFlowsResponse, GlobalFlowsSummary
from src.api.schemas.macro_pulse import ChartCoverage, ChartInsight, ChartRecord, ChartSeriesMetadata
from src.api.services.global_flows import build_global_flows_insights, build_global_flows_summary
from src.etl.prepare_datasets.global_flows import prepare_global_flows_kpis
from src.utilities.config_loader import load_config


ORDER = ("GF1", "GF2", "GF3")
TABLES = {chart: f"chart_global_flows_{chart.lower()}" for chart in ORDER}


class GlobalFlowsDataError(RuntimeError): pass


def _load(conn: sqlite3.Connection, chart: str) -> pd.DataFrame:
    try: return pd.read_sql_query(f"SELECT * FROM {TABLES[chart]} ORDER BY date ASC", conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc: raise GlobalFlowsDataError(f"Prepared table unavailable for {chart}") from exc


def _coverage(frame: pd.DataFrame, metrics: list[str]) -> ChartCoverage:
    available = [metric for metric in metrics if metric in frame.columns]
    long = frame.melt(id_vars=["date"], value_vars=available, var_name="metric_id", value_name="value") if available else pd.DataFrame(columns=["date", "metric_id", "value"])
    report = coverage_report(long, metrics)
    return ChartCoverage(requested_metrics=report["requested_metrics"], available_metrics=report["present_metrics"], missing_metrics=report["missing_metrics"], first_observation=report["first_valid_date"], latest_observation=report["latest_valid_date"], valid_observations=report["valid_observations"])


def _records(frame: pd.DataFrame, metrics: list[str]) -> list[ChartRecord]:
    result = []
    for _, row in frame.iterrows():
        date = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(date): continue
        values = {metric: None if metric not in frame or pd.isna(row.get(metric)) else float(row.get(metric)) for metric in metrics}
        for metric in metrics:
            raw = metric.removesuffix("_normalised")
            if raw in frame: values[raw] = None if pd.isna(row.get(raw)) else float(row.get(raw))
        result.append(ChartRecord(date=date.date(), values=values))
    return result


def build_global_flows_response(conn: sqlite3.Connection) -> GlobalFlowsResponse:
    config = load_config("charts", "GlobalFlows")
    datasets = {chart: _load(conn, chart) for chart in ORDER}; kpis = prepare_global_flows_kpis(conn)
    summary = build_global_flows_summary(kpis, datasets["GF1"], datasets["GF3"]); insights = {item["chart_id"]: item for item in build_global_flows_insights(datasets)}
    charts = []
    for chart in ORDER:
        cfg = config[chart]; metrics = list(cfg.get("metrics", [])); optional = list(cfg.get("optional_metrics", [])); all_metrics = metrics + optional
        labels = cfg.get("metric_labels", {}); units = cfg.get("units", {}); roles = cfg.get("roles", {}); axes = cfg.get("axes", {})
        metadata = [ChartSeriesMetadata(metric=metric, label=labels.get(metric, metric), unit=units.get(metric, "Index"), role=roles.get(metric, "line"), axis=axes.get(metric, "left"), display_order=index, optional=metric in optional) for index, metric in enumerate(all_metrics, start=1)]
        baseline = None
        if "baseline_date" in datasets[chart] and not datasets[chart]["baseline_date"].dropna().empty: baseline = pd.to_datetime(datasets[chart]["baseline_date"].dropna().iloc[0]).date().isoformat()
        charts.append(GlobalFlowsChart(id=chart, title=cfg["name"], description=cfg["description"], frequency=cfg["frequency"], chart_type=cfg["chart_type"], series_metadata=metadata, records=_records(datasets[chart], all_metrics), insight=ChartInsight(**insights[chart]) if chart in insights else None, coverage=_coverage(datasets[chart], all_metrics), baseline_date=baseline))
    return GlobalFlowsResponse(page=GlobalFlowsPage(id="global_flows", title="Currency, Commodities & Fixed Income", description="Track sterling, UK bond assets and global commodity-price conditions."), summary=GlobalFlowsSummary(**summary), kpis=[GlobalFlowsKPI(id=row["kpi_id"], metric=row["metric_id"], name=row["name"], value=row["value"], delta=row["delta"], description=row["description"], date=row["date"].isoformat() if row.get("date") else None, main_unit=row["main_unit"], delta_unit=row["delta_unit"], comparison_label=row["comparison_label"], delta_direction=row["delta_direction"]) for row in kpis], charts=charts)
