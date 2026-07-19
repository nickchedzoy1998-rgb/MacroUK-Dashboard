"""Assembly of the Financial Markets and Equities API response."""

from __future__ import annotations

import sqlite3

import pandas as pd

from src.analytics.chart_transforms import coverage_report
from src.api.schemas.financial_markets import FinancialMarketsChart, FinancialMarketsKPI, FinancialMarketsPage, FinancialMarketsResponse, FinancialMarketsSummary
from src.api.schemas.macro_pulse import ChartCoverage, ChartInsight, ChartRecord, ChartSeriesMetadata
from src.api.services.financial_markets import build_financial_markets_insights, build_financial_markets_summary
from src.etl.prepare_datasets.financial_markets import prepare_financial_markets_kpis
from src.utilities.config_loader import load_config


ORDER = ("FM1", "FM2", "FM3")
TABLES = {"FM1": "chart_financial_markets_fm1", "FM2": "chart_financial_markets_fm2_monthly", "FM3": "chart_financial_markets_fm3"}


class FinancialMarketsDataError(RuntimeError):
    pass


def _load(conn: sqlite3.Connection, chart_id: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(f"SELECT * FROM {TABLES[chart_id]} ORDER BY date ASC", conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        raise FinancialMarketsDataError(f"Prepared table unavailable for {chart_id}") from exc


def _coverage(frame: pd.DataFrame, metrics: list[str]) -> ChartCoverage:
    available = [metric for metric in metrics if metric in frame.columns]
    long = frame.melt(id_vars=["date"], value_vars=available, var_name="metric_id", value_name="value") if available else pd.DataFrame(columns=["date", "metric_id", "value"])
    report = coverage_report(long, metrics)
    return ChartCoverage(requested_metrics=report["requested_metrics"], available_metrics=report["present_metrics"], missing_metrics=report["missing_metrics"], first_observation=report["first_valid_date"], latest_observation=report["latest_valid_date"], valid_observations=report["valid_observations"])


def _records(frame: pd.DataFrame, metrics: list[str]) -> list[ChartRecord]:
    rows = []
    for _, row in frame.iterrows():
        date = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(date):
            continue
        values = {metric: None if metric not in frame or pd.isna(row.get(metric)) else float(row.get(metric)) for metric in metrics}
        for metric in metrics:
            raw_metric = metric.removesuffix("_normalised")
            if raw_metric in frame:
                values[raw_metric] = None if pd.isna(row.get(raw_metric)) else float(row.get(raw_metric))
        rows.append(ChartRecord(date=date.date(), values=values))
    return rows


def build_financial_markets_response(conn: sqlite3.Connection) -> FinancialMarketsResponse:
    config = load_config("charts", "FinancialMarkets")
    datasets = {chart: _load(conn, chart) for chart in ORDER}
    kpis = prepare_financial_markets_kpis(conn)
    summary = build_financial_markets_summary(kpis, datasets["FM1"], datasets["FM3"])
    insights = {item["chart_id"]: item for item in build_financial_markets_insights(datasets)}
    charts = []
    for chart_id in ORDER:
        cfg = config[chart_id]
        configured = list(cfg.get("metrics", []))
        if chart_id in {"FM1", "FM3"}:
            metrics = [metric for metric in configured if not metric.endswith("_normalised")]
            plotted = [f"{metric}_normalised" for metric in metrics]
            labels = {f"{metric}_normalised": cfg.get("metric_labels", {}).get(metric, metric) for metric in metrics}
            units = {metric: "Index" for metric in plotted}
        else:
            plotted = configured
            labels = cfg.get("metric_labels", {})
            units = cfg.get("units", {})
        roles = cfg.get("roles", {}); axes = cfg.get("axes", {})
        metadata = [ChartSeriesMetadata(metric=metric, label=labels.get(metric, metric), unit=units.get(metric, "Index"), role=roles.get(metric, "line"), axis=axes.get(metric, "left"), display_order=index, optional=False) for index, metric in enumerate(plotted, start=1)]
        baseline = None
        if "baseline_date" in datasets[chart_id] and not datasets[chart_id]["baseline_date"].dropna().empty:
            baseline = pd.to_datetime(datasets[chart_id]["baseline_date"].dropna().iloc[0]).date().isoformat()
        charts.append(FinancialMarketsChart(id=chart_id, title=cfg["name"], description=cfg["description"], frequency=cfg["frequency"], chart_type=cfg["chart_type"], series_metadata=metadata, records=_records(datasets[chart_id], plotted), insight=ChartInsight(**insights[chart_id]) if chart_id in insights else None, coverage=_coverage(datasets[chart_id], plotted), baseline_date=baseline))
    return FinancialMarketsResponse(page=FinancialMarketsPage(id="financial_markets", title="Financial Markets & Equities", description="Track UK equity tiers, listed housebuilders and selected company proxies."), summary=FinancialMarketsSummary(**summary), kpis=[FinancialMarketsKPI(id=row["kpi_id"], metric=row["metric_id"], name=row["name"], value=row["value"], delta=row["delta"], description=row["description"], date=row["date"].isoformat() if row.get("date") else None, main_unit=row["main_unit"], delta_unit=row["delta_unit"], comparison_label=row["comparison_label"], delta_direction=row["delta_direction"]) for row in kpis], charts=charts)
