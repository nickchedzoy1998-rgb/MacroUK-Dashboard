"""Assembly of the Housing and Consumer Credit API response."""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd

from src.analytics.chart_transforms import coverage_report
from src.api.schemas.housing_credit import HousingCreditChart, HousingCreditKPI, HousingCreditPage, HousingCreditResponse, HousingCreditSummary
from src.api.schemas.macro_pulse import ChartCoverage, ChartInsight, ChartRecord, ChartSeriesMetadata
from src.api.services.housing_credit import build_housing_credit_insights, build_housing_credit_summary
from src.etl.prepare_datasets.housing_credit import prepare_housing_credit_kpis
from src.utilities.config_loader import load_config, resolve_metric_label


ORDER = ("HC1", "HC2", "HC3", "HC4")
TABLES = {chart: f"chart_housing_credit_{chart.lower()}" for chart in ORDER}


class HousingCreditDataError(RuntimeError):
    pass


def _load(conn: sqlite3.Connection, chart: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(f"SELECT * FROM {TABLES[chart]} ORDER BY date ASC", conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        raise HousingCreditDataError(f"Prepared table unavailable for {chart}") from exc


def _coverage(frame: pd.DataFrame, metrics: list[str]) -> ChartCoverage:
    available = [metric for metric in metrics if metric in frame.columns]
    long = frame.melt(id_vars=["date"], value_vars=available, var_name="metric_id", value_name="value") if available else pd.DataFrame(columns=["date", "metric_id", "value"])
    report = coverage_report(long, metrics)
    return ChartCoverage(requested_metrics=report["requested_metrics"], available_metrics=report["present_metrics"], missing_metrics=report["missing_metrics"], first_observation=report["first_valid_date"], latest_observation=report["latest_valid_date"], valid_observations=report["valid_observations"])


def _records(frame: pd.DataFrame, metrics: list[str]) -> list[ChartRecord]:
    records = []
    for _, row in frame.iterrows():
        parsed = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(parsed): continue
        records.append(ChartRecord(date=parsed.date(), values={metric: None if metric not in frame or pd.isna(row.get(metric)) else float(row.get(metric)) for metric in metrics}))
    return records


def build_housing_credit_response(conn: sqlite3.Connection) -> HousingCreditResponse:
    config = load_config("charts", "HousingCredit")
    datasets = {chart: _load(conn, chart) for chart in ORDER}
    kpis = prepare_housing_credit_kpis(conn)
    summary = build_housing_credit_summary(kpis, datasets["HC4"])
    insight_map = {item["chart_id"]: item for item in build_housing_credit_insights(datasets)}
    charts = []
    for chart in ORDER:
        cfg = config[chart]
        metrics = list(cfg.get("metrics", [])); optional = list(cfg.get("optional_metrics", [])); all_metrics = metrics + optional
        if chart == "HC2":
            source_metrics = metrics
            metrics = [f"{metric}_normalised" for metric in source_metrics]
            all_metrics = metrics
            labels = {
                f"{metric}_normalised": f"{resolve_metric_label(metric, cfg.get('metric_labels', {}))} (rebased)"
                for metric in source_metrics
            }
            units = {metric: "Index" for metric in metrics}
            roles = {metric: "line" for metric in metrics}; axes = {metric: "left" for metric in metrics}
        else:
            labels = cfg.get("metric_labels", {}); units = cfg.get("units", {}); roles = cfg.get("roles", {}); axes = cfg.get("axes", {})
        metadata = [ChartSeriesMetadata(metric=metric, label=resolve_metric_label(metric, labels), unit=units.get(metric, "%"), role=roles.get(metric, "line"), axis=axes.get(metric, "left"), display_order=index, optional=metric in optional) for index, metric in enumerate(all_metrics, start=1)]
        baseline = None
        if chart == "HC2" and not datasets[chart].empty:
            baseline_value = datasets[chart]["baseline_date"].dropna().iloc[0] if "baseline_date" in datasets[chart] else None
            baseline = pd.to_datetime(baseline_value).date().isoformat() if baseline_value is not None else None
        charts.append(HousingCreditChart(id=chart, title=cfg["name"], description=cfg["description"], frequency=cfg["frequency"], chart_type=cfg["chart_type"], series_metadata=metadata, records=_records(datasets[chart], all_metrics), insight=ChartInsight(**insight_map[chart]) if chart in insight_map else None, coverage=_coverage(datasets[chart], list(cfg.get("metrics", []))), baseline_date=baseline, geography="England and Wales" if chart == "HC3" else None, zero_reference=0.0 if chart == "HC4" else None))
    return HousingCreditResponse(page=HousingCreditPage(id="housing_credit", title="Housing Market & Consumer Credit", description="Track mortgage conditions, property activity and household borrowing."), summary=HousingCreditSummary(**summary), kpis=[HousingCreditKPI(id=row["kpi_id"], metric=row["metric_id"], name=row["name"], value=row["value"], delta=row["delta"], description=row["description"], date=row["date"].isoformat() if row.get("date") else None, main_unit=row["main_unit"], delta_unit=row["delta_unit"], comparison_label=row["comparison_label"], delta_direction=row["delta_direction"]) for row in kpis], charts=charts)
