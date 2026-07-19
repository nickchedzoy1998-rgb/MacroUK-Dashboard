"""Deterministic Macro Pulse summary and chart insight rules."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd


GDP_FLAT_THRESHOLD = 0.1
GDP_MODEST_THRESHOLD = 0.5
INFLATION_MATERIAL_GAP = 1.0
INFLATION_MODERATE_GAP = 0.3
INFLATION_NEAR_GAP = 0.3
CHANGE_EPSILON = 0.05
ELEVATED_WAGE_GROWTH = 5.0


def growth_state(value: float | None) -> str | None:
    if value is None:
        return None
    if value < 0:
        return "contracting"
    if value <= GDP_FLAT_THRESHOLD:
        return "broadly flat"
    if value <= GDP_MODEST_THRESHOLD:
        return "growing modestly"
    return "showing stronger growth"


def inflation_state(value: float | None, target: float = 2.0) -> str | None:
    if value is None:
        return None
    gap = value - target
    if gap >= INFLATION_MATERIAL_GAP:
        return "materially above target"
    if gap >= INFLATION_MODERATE_GAP:
        return "moderately above target"
    if gap >= -INFLATION_NEAR_GAP:
        return "near target"
    return "below target"


def change_direction(delta: float | None) -> str | None:
    if delta is None:
        return None
    if delta > CHANGE_EPSILON:
        return "rising"
    if delta < -CHANGE_EPSILON:
        return "easing"
    return "broadly stable"


def _kpi_map(kpis: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(kpi.get("kpi_id")): kpi for kpi in kpis}


def _value(kpi_map: Mapping[str, Mapping[str, Any]], key: str) -> float | None:
    value = kpi_map.get(key, {}).get("value")
    return None if value is None else float(value)


def _delta(kpi_map: Mapping[str, Mapping[str, Any]], key: str) -> float | None:
    value = kpi_map.get(key, {}).get("delta")
    return None if value is None else float(value)


def _latest_change(frame: pd.DataFrame, metric: str) -> tuple[float | None, float | None, pd.Timestamp | None]:
    if frame is None or metric not in frame.columns:
        return None, None, None
    values = frame[["date", metric]].copy()
    values[metric] = pd.to_numeric(values[metric], errors="coerce")
    values = values.dropna(subset=["date", metric]).sort_values("date")
    if values.empty:
        return None, None, None
    latest = float(values.iloc[-1][metric])
    previous = float(values.iloc[-2][metric]) if len(values) >= 2 else None
    return latest, previous, pd.Timestamp(values.iloc[-1]["date"])


def _direction_from_change(current: float | None, previous: float | None) -> str | None:
    if current is None or previous is None:
        return None
    if current > previous + CHANGE_EPSILON:
        return "rising"
    if current < previous - CHANGE_EPSILON:
        return "easing"
    return "stable"


def build_macro_pulse_summary(
    kpis: Sequence[Mapping[str, Any]],
    labour_data: pd.DataFrame | None = None,
    *,
    inflation_target: float = 2.0,
) -> dict[str, str]:
    """Build a cautious overview from whatever current components are available."""
    mapped = _kpi_map(kpis)
    parts: list[str] = []
    body: list[str] = []

    growth = growth_state(_value(mapped, "GDP_GROWTH"))
    if growth:
        growth_headline = {
            "contracting": "growth is contracting",
            "broadly flat": "growth is broadly flat",
            "growing modestly": "growth is modest",
            "showing stronger growth": "growth is stronger",
        }[growth]
        parts.append(growth_headline)
        body.append(f"The latest quarterly GDP reading is {growth}.")

    inflation = inflation_state(_value(mapped, "INFLATION"), inflation_target)
    if inflation:
        parts.append(f"inflation is {inflation}")
        body.append(f"Headline inflation is {inflation} relative to the {inflation_target:.0f}% target.")

    unemployment_change = change_direction(_delta(mapped, "UNEMPLOYMENT"))
    wage_change = change_direction(_delta(mapped, "WAGE_GROWTH"))
    employment_change = None
    if labour_data is not None:
        employment, employment_previous, _ = _latest_change(labour_data, "EMPRATE")
        employment_change = _direction_from_change(employment, employment_previous)

    labour_signals = []
    if unemployment_change == "rising" or employment_change == "easing":
        labour_signals.append("softening")
    elif unemployment_change == "easing" or employment_change == "rising":
        labour_signals.append("improving")
    elif unemployment_change in {"stable", "broadly stable"} or employment_change in {"stable", "broadly stable"}:
        labour_signals.append("stable")

    if "softening" in labour_signals and "improving" in labour_signals:
        labour_state = "broadly stable"
    elif "softening" in labour_signals:
        labour_state = "softening"
    elif "improving" in labour_signals:
        labour_state = "improving"
    elif "stable" in labour_signals:
        labour_state = "broadly stable"
    else:
        labour_state = None

    if labour_state:
        parts.append(f"labour conditions are {labour_state}")
        body.append(f"Labour conditions are {labour_state} on the latest available changes.")
    if wage_change:
        wage_phrase = "wage growth is easing" if wage_change == "easing" else f"wage growth is {wage_change}"
        if _value(mapped, "WAGE_GROWTH") is not None and _value(mapped, "WAGE_GROWTH") >= ELEVATED_WAGE_GROWTH:
            wage_phrase += " but remains elevated"
        body.append(wage_phrase.capitalize() + ".")

    headline = "Macro Pulse conditions are not available."
    if parts:
        headline = "; ".join(parts).capitalize() + "."
    return {"headline": headline, "body": " ".join(body)}


def build_macro_pulse_insights(
    datasets: Mapping[str, pd.DataFrame],
    *,
    inflation_target: float = 2.0,
) -> list[dict[str, Any]]:
    """Return one deterministic insight for each Macro Pulse chart."""
    insights: list[dict[str, Any]] = []

    growth_data = datasets.get("EGM")
    qoq, qoq_previous, qoq_date = _latest_change(growth_data, "GDP_QOQ") if growth_data is not None else (None, None, None)
    yoy, yoy_previous, yoy_date = _latest_change(growth_data, "GDP_YOY") if growth_data is not None else (None, None, None)
    if qoq is not None or yoy is not None:
        growth_parts = []
        if qoq is not None:
            growth_parts.append(f"Latest quarterly GDP is {growth_state(qoq)}")
        if yoy is not None and yoy_previous is not None:
            annual_direction = "strengthening" if yoy > yoy_previous + CHANGE_EPSILON else "easing" if yoy < yoy_previous - CHANGE_EPSILON else "broadly stable"
            growth_parts.append(f"Annual growth is {annual_direction}")
        insights.append(
            {
                "chart_id": "EGM",
                "headline": "Growth momentum",
                "body": ". ".join(growth_parts) + ".",
                "direction": "negative" if qoq is not None and qoq < 0 else "positive" if qoq is not None and qoq > GDP_FLAT_THRESHOLD else "neutral",
                "as_of_date": max(date for date in (qoq_date, yoy_date) if date is not None).date().isoformat(),
            }
        )

    inflation_data = datasets.get("IB")
    cpi, _, cpi_date = _latest_change(inflation_data, "CPI") if inflation_data is not None else (None, None, None)
    core, _, core_date = _latest_change(inflation_data, "CORE_CPI") if inflation_data is not None else (None, None, None)
    if cpi is not None or core is not None:
        inflation_parts = []
        if cpi is not None:
            gap = cpi - inflation_target
            inflation_parts.append(f"CPI is {abs(gap):.1f} percentage points {'above' if gap >= 0 else 'below'} the target")
        if core is not None and cpi is not None:
            inflation_parts.append(f"Core CPI is {'above' if core > cpi else 'below' if core < cpi else 'at'} headline CPI")
        elif core is not None:
            inflation_parts.append("Core CPI is available; headline CPI is not available")
        insights.append(
            {
                "chart_id": "IB",
                "headline": "Inflation pressures",
                "body": ". ".join(inflation_parts) + ".",
                "direction": "negative" if cpi is not None and cpi > inflation_target + INFLATION_MODERATE_GAP else "positive" if cpi is not None and cpi < inflation_target - INFLATION_MODERATE_GAP else "neutral",
                "as_of_date": max(date for date in (cpi_date, core_date) if date is not None).date().isoformat(),
            }
        )

    labour_data = datasets.get("LBH")
    labour_changes = []
    dates = []
    for metric in ("UNRATE", "EMPRATE", "WAGE_GROWTH"):
        current, previous, latest_date = _latest_change(labour_data, metric) if labour_data is not None else (None, None, None)
        if current is not None:
            dates.append(latest_date)
        if current is not None and previous is not None:
            labour_changes.append((metric, _direction_from_change(current, previous)))
    if dates:
        labels = {"UNRATE": "Unemployment", "EMPRATE": "Employment", "WAGE_GROWTH": "Wage growth"}
        descriptions = [f"{labels[metric]} is {direction}" for metric, direction in labour_changes]
        positive = sum(1 for metric, direction in labour_changes if (metric == "UNRATE" and direction == "easing") or (metric != "UNRATE" and direction == "rising"))
        negative = sum(1 for metric, direction in labour_changes if (metric == "UNRATE" and direction == "rising") or (metric != "UNRATE" and direction == "easing"))
        direction = "positive" if positive and not negative else "negative" if negative and not positive else "neutral"
        insights.append(
            {
                "chart_id": "LBH",
                "headline": "Labour market health",
                "body": ("; ".join(descriptions).capitalize() + ".") if descriptions else "Latest labour-market levels are available, but comparison data is limited.",
                "direction": direction,
                "as_of_date": max(dates).date().isoformat(),
            }
        )

    return insights
