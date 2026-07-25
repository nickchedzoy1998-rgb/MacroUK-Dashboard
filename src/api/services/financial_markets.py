"""Deterministic interpretation rules for Financial Markets and Equities."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.utilities.config_loader import load_config, resolve_metric_label


EPSILON = 0.05


def _latest(frame: pd.DataFrame | None, column: str) -> tuple[float | None, float | None, pd.Timestamp | None]:
    if frame is None or column not in frame.columns:
        return None, None, None
    rows = frame[["date", column]].copy()
    rows[column] = pd.to_numeric(rows[column], errors="coerce")
    rows = rows.dropna(subset=["date", column]).sort_values("date")
    if rows.empty:
        return None, None, None
    return float(rows.iloc[-1][column]), float(rows.iloc[-2][column]) if len(rows) > 1 else None, pd.Timestamp(rows.iloc[-1]["date"])


def _direction(value: float | None) -> str:
    if value is None or abs(value) <= EPSILON:
        return "broadly stable"
    return "positive" if value > 0 else "negative"


def _display_labels(chart_id: str) -> dict[str, str]:
    config = load_config("charts", "FinancialMarkets", chart_id) or {}
    return {
        metric: str(label).replace(" (rebased)", "")
        for metric, label in config.get("metric_labels", {}).items()
    }


def _proxy_rank(
    frame: pd.DataFrame | None,
    labels: Mapping[str, str] | None = None,
) -> tuple[str | None, float | None, str | None, float | None]:
    if frame is None:
        return None, None, None, None
    columns = [column for column in frame.columns if column.endswith("_return_21d")]
    if not columns:
        return None, None, None, None
    valid = frame.drop(columns=[], errors="ignore").sort_values("date")
    if valid.empty:
        return None, None, None, None
    latest = valid.iloc[-1]
    values = {column: float(latest[column]) for column in columns if pd.notna(latest[column])}
    if not values:
        return None, None, None, None
    best = max(values, key=values.get)
    worst = min(values, key=values.get)
    best_metric = best.removesuffix("_return_21d")
    worst_metric = worst.removesuffix("_return_21d")
    return (
        resolve_metric_label(best_metric, labels),
        values[best],
        resolve_metric_label(worst_metric, labels),
        values[worst],
    )


def build_financial_markets_summary(kpis: list[Mapping[str, Any]], fm1: pd.DataFrame | None = None, fm3: pd.DataFrame | None = None) -> dict[str, str]:
    mapped = {str(kpi.get("kpi_id")): kpi for kpi in kpis}
    broad = [mapped[key].get("value") for key in ("FTSE_100", "FTSE_250") if key in mapped]
    parts: list[str] = []
    if broad:
        parts.append(f"the tracked large and mid-cap indices are {_direction(sum(float(v) for v in broad) / len(broad))} over one month")
    relative = mapped.get("FTSE_250_RELATIVE", {}).get("value")
    if relative is not None:
        parts.append(f"the FTSE 250 is {('ahead of' if relative > EPSILON else 'behind' if relative < -EPSILON else 'roughly in line with')} the FTSE 100 over the same period")
    best, best_value, worst, worst_value = _proxy_rank(fm3, _display_labels("FM3"))
    if best and worst:
        parts.append(f"among the tracked company proxies, {best} is strongest and {worst} weakest over one month")
    headline = "Financial market indicators are not available."
    if parts:
        headline = "; ".join(parts).capitalize() + "."
    body = "The comparison uses market-price performance and does not represent a complete measure of the UK economy or any sector."
    if best_value is not None and worst_value is not None:
        body += f" The selected company proxies range from {best_value:.1f}% to {worst_value:.1f}% over the latest 21 trading observations."
    return {"headline": headline, "body": body}


def build_financial_markets_insights(datasets: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    fm1_labels = _display_labels("FM1")
    fm2_labels = _display_labels("FM2")
    fm3_labels = _display_labels("FM3")
    fm1 = datasets.get("FM1")
    normalised = [column for column in ("FTSE_100_close_normalised", "FTSE_250_close_normalised", "FTSE_AIM_close_normalised") if fm1 is not None and column in fm1.columns]
    if normalised and fm1 is not None:
        valid = fm1.dropna(subset=normalised)
        if not valid.empty:
            latest = valid.iloc[-1]; values = {column: float(latest[column]) for column in normalised}
            best = resolve_metric_label(max(values, key=values.get), fm1_labels)
            worst = resolve_metric_label(min(values, key=values.get), fm1_labels)
            relative = latest.get("FTSE_250_close_return_21d")
            compared = f" The FTSE 250 one-month return is {float(relative):.1f}%." if pd.notna(relative) else ""
            insights.append({"chart_id": "FM1", "headline": "UK equity-tier performance", "body": f"{best} is highest and {worst} lowest at the latest common rebased observation.{compared}", "direction": "positive" if values["FTSE_100_close_normalised"] >= 100 else "negative", "as_of_date": pd.Timestamp(latest.date).date().isoformat()})
    fm2 = datasets.get("FM2_MONTHLY")
    normalised = [column for column in ("EQ_TW_close_normalised", "EQ_BAR_close_normalised", "UK_HPI_INDEX_UK_normalised") if fm2 is not None and column in fm2.columns]
    if normalised and fm2 is not None:
        valid = fm2.dropna(subset=normalised)
        if not valid.empty:
            latest = valid.iloc[-1]
            values = {column: float(latest[column]) for column in normalised}
            best = resolve_metric_label(max(values, key=values.get), fm2_labels)
            insights.append({"chart_id": "FM2", "headline": "Housebuilder and HPI comparison", "body": f"{best} has the highest rebased value at the latest common month-end. This is a descriptive price comparison, not evidence that share prices determine future housing outcomes.", "direction": "neutral", "as_of_date": pd.Timestamp(latest.date).date().isoformat()})
    fm3 = datasets.get("FM3")
    best, best_value, worst, worst_value = _proxy_rank(fm3, fm3_labels)
    if best and worst and fm3 is not None:
        latest_date = pd.to_datetime(fm3.date).max()
        insights.append({"chart_id": "FM3", "headline": "Selected company proxies", "body": f"{best} is strongest at {best_value:.1f}% and {worst} weakest at {worst_value:.1f}% over one month. These proxies do not represent complete sector indices.", "direction": "neutral", "as_of_date": latest_date.date().isoformat()})
    return insights
