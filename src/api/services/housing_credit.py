"""Deterministic Housing and Consumer Credit interpretation rules."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd

from src.utilities.config_loader import load_config, resolve_metric_label


CHANGE_EPSILON = 0.05


def _latest(frame: pd.DataFrame, metric: str) -> tuple[float | None, float | None, pd.Timestamp | None]:
    if frame is None or metric not in frame.columns: return None, None, None
    rows = frame[["date", metric]].copy(); rows[metric] = pd.to_numeric(rows[metric], errors="coerce"); rows = rows.dropna(subset=["date", metric]).sort_values("date")
    if rows.empty: return None, None, None
    return float(rows.iloc[-1][metric]), float(rows.iloc[-2][metric]) if len(rows) > 1 else None, pd.Timestamp(rows.iloc[-1].date)


def _state(value: float | None) -> str | None:
    if value is None: return None
    return "rising" if value > CHANGE_EPSILON else "falling" if value < -CHANGE_EPSILON else "broadly stable"


def build_housing_credit_summary(kpis: Sequence[Mapping[str, Any]], hc4: pd.DataFrame | None = None) -> dict[str, str]:
    mapped = {str(kpi.get("kpi_id")): kpi for kpi in kpis}; parts = []; body = []
    mortgage = mapped.get("MORTGAGE_RATE", {}); house = mapped.get("HOUSE_PRICE_GROWTH", {})
    if mortgage.get("value") is not None:
        parts.append(f"mortgage rates are {_state(mortgage.get('delta'))}"); body.append(f"The two-year mortgage rate is {float(mortgage['value']):.2f}% and is {_state(mortgage.get('delta')) or 'without a comparison change'} from the previous observation.")
    if house.get("value") is not None:
        parts.append("house-price growth is positive" if float(house["value"]) >= 0 else "house-price growth is negative"); body.append(f"Annual UK house-price growth is {float(house['value']):.1f}%.")
    secured, _, _ = _latest(hc4, "NET_LENDING_DWELLINGS_MO") if hc4 is not None else (None, None, None); consumer, _, _ = _latest(hc4, "NET_CONSUMER_CREDIT_MO") if hc4 is not None else (None, None, None)
    if secured is not None or consumer is not None:
        parts.append("household borrowing signals are mixed" if secured is not None and consumer is not None and (secured >= 0) != (consumer >= 0) else "household borrowing is moving in the same direction")
    headline = "Housing and credit conditions are not available."
    if parts:
        text = "; ".join(parts); headline = text[:1].upper() + text[1:] + "."
    return {"headline": headline, "body": " ".join(body)}


def build_housing_credit_insights(datasets: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    result = []
    hc1 = datasets.get("HC1"); mortgage, mortgage_previous, mortgage_date = _latest(hc1, "MORTGAGE_2YR_75LTV_MO") if hc1 is not None else (None, None, None); house, _, house_date = _latest(hc1, "UK_HPI_YOY_CHANGE_UK") if hc1 is not None else (None, None, None)
    if mortgage is not None or house is not None: result.append({"chart_id": "HC1", "headline": "Mortgage and house-price momentum", "body": f"Mortgage rates are {_state(mortgage - mortgage_previous) if mortgage is not None and mortgage_previous is not None else 'available'}; annual house-price growth is {house:.1f}%" if house is not None else "Mortgage-rate data is available; house-price growth is not available.", "direction": "negative" if mortgage is not None and mortgage_previous is not None and mortgage > mortgage_previous else "positive" if house is not None and house >= 0 else "neutral", "as_of_date": max(d for d in (mortgage_date, house_date) if d is not None).date().isoformat()})
    hc2 = datasets.get("HC2"); normalised = [column for column in hc2.columns if column.endswith("_normalised")] if hc2 is not None else []
    if normalised:
        labels = (load_config("charts", "HousingCredit", "HC2") or {}).get("metric_labels", {})
        latest = hc2.dropna(subset=normalised).iloc[-1]
        values = {column: float(latest[column]) for column in normalised}
        highest = resolve_metric_label(max(values, key=values.get), labels)
        lowest = resolve_metric_label(min(values, key=values.get), labels)
        result.append({"chart_id": "HC2", "headline": "Regional housing divergence", "body": f"{highest} has the highest rebased value and {lowest} the lowest at the latest common observation.", "direction": "neutral", "as_of_date": pd.Timestamp(latest.date).date().isoformat()})
    hc3 = datasets.get("HC3"); cash, _, cash_date = _latest(hc3, "CASH_SHARE_PCT") if hc3 is not None else (None, None, None)
    if cash is not None: result.append({"chart_id": "HC3", "headline": "Buyer composition", "body": f"Cash-financed transactions represent {cash:.1f}% of the derived England-and-Wales total at the latest valid observation.", "direction": "neutral", "as_of_date": cash_date.date().isoformat()})
    hc4 = datasets.get("HC4"); secured, _, secured_date = _latest(hc4, "NET_LENDING_DWELLINGS_MO") if hc4 is not None else (None, None, None); consumer, _, consumer_date = _latest(hc4, "NET_CONSUMER_CREDIT_MO") if hc4 is not None else (None, None, None)
    if secured is not None or consumer is not None:
        secured_text = f"Net secured lending is {secured:.0f} GBP millions" if secured is not None else "Net secured lending is unavailable"
        consumer_text = f"net consumer credit is {consumer:.0f} GBP millions" if consumer is not None else "net consumer credit is unavailable"
        result.append({"chart_id": "HC4", "headline": "Household borrowing", "body": f"{secured_text}; {consumer_text}.", "direction": "neutral", "as_of_date": max(d for d in (secured_date, consumer_date) if d is not None).date().isoformat()})
    return result
