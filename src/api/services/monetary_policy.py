"""Deterministic Monetary Policy and Liquidity interpretation rules."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd


POLICY_RESTRICTIVE_THRESHOLD = 3.0
SPREAD_ALIGNMENT_THRESHOLD = 0.25
CHANGE_EPSILON = 0.05


def _kpis(kpis: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(kpi.get("kpi_id")): kpi for kpi in kpis}


def _value(kpis: Mapping[str, Mapping[str, Any]], key: str) -> float | None:
    value = kpis.get(key, {}).get("value")
    return None if value is None else float(value)


def _delta(kpis: Mapping[str, Mapping[str, Any]], key: str) -> float | None:
    value = kpis.get(key, {}).get("delta")
    return None if value is None else float(value)


def _direction(delta: float | None) -> str | None:
    if delta is None:
        return None
    if delta > CHANGE_EPSILON:
        return "rising"
    if delta < -CHANGE_EPSILON:
        return "falling"
    return "broadly stable"


def build_monetary_policy_summary(kpis: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    mapped = _kpis(kpis)
    parts = []
    body = []
    bank = _value(mapped, "BANK_RATE")
    bank_direction = _direction(_delta(mapped, "BANK_RATE"))
    if bank is not None:
        level = "restrictive" if bank >= POLICY_RESTRICTIVE_THRESHOLD else "below the configured restrictive threshold"
        parts.append(f"policy settings are {level}")
        body.append(f"Bank Rate is {bank:.2f}% and has been {bank_direction or 'unchanged'} at the latest distinct rate comparison.")
    spread = _value(mapped, "BANK_RATE_SONIA_SPREAD")
    if spread is not None:
        aligned = abs(spread) <= SPREAD_ALIGNMENT_THRESHOLD
        parts.append("overnight rates are close to Bank Rate" if aligned else "overnight rates differ from Bank Rate")
        body.append(f"The latest Bank Rate–SONIA spread is {spread:+.2f} percentage points.")
    m4 = _value(mapped, "M4_GROWTH_MO")
    m4_direction = _direction(_delta(mapped, "M4_GROWTH_MO"))
    if m4 is not None:
        parts.append(f"money growth is {m4_direction or 'available'}")
        body.append(f"M4 growth is {m4:.1f}% and is {m4_direction or 'without a comparison change'} from the previous monthly observation.")
    headline = "Monetary policy conditions are not available."
    if parts:
        text = "; ".join(parts)
        headline = text[:1].upper() + text[1:] + "."
    return {"headline": headline, "body": " ".join(body)}


def _latest(frame: pd.DataFrame, metric: str) -> tuple[float | None, float | None, pd.Timestamp | None]:
    if frame is None or metric not in frame.columns:
        return None, None, None
    rows = frame[["date", metric]].copy()
    rows[metric] = pd.to_numeric(rows[metric], errors="coerce")
    rows = rows.dropna(subset=["date", metric]).sort_values("date")
    if rows.empty:
        return None, None, None
    return float(rows.iloc[-1][metric]), float(rows.iloc[-2][metric]) if len(rows) > 1 else None, pd.Timestamp(rows.iloc[-1]["date"])


def build_monetary_policy_insights(datasets: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    insights = []
    mp1 = datasets.get("MP1")
    bank, _, bank_date = _latest(mp1, "BANK_RATE_DA") if mp1 is not None else (None, None, None)
    sonia, _, sonia_date = _latest(mp1, "SONIA") if mp1 is not None else (None, None, None)
    spread, previous_spread, spread_date = _latest(mp1, "BANK_RATE_SONIA_SPREAD") if mp1 is not None else (None, None, None)
    if any(value is not None for value in (bank, sonia, spread)):
        movement = "widening" if spread is not None and previous_spread is not None and spread > previous_spread + CHANGE_EPSILON else "narrowing" if spread is not None and previous_spread is not None and spread < previous_spread - CHANGE_EPSILON else "broadly stable"
        text = []
        if bank is not None: text.append(f"Bank Rate is {bank:.2f}%")
        if sonia is not None: text.append(f"SONIA is {sonia:.2f}%")
        if spread is not None: text.append(f"the spread is {spread:+.2f} percentage points and is {movement}")
        insights.append({"chart_id": "MP1", "headline": "Policy and market rates", "body": ". ".join(text) + ".", "direction": "neutral", "as_of_date": max(d for d in (bank_date, sonia_date, spread_date) if d is not None).date().isoformat()})

    mp2 = datasets.get("MP2")
    m4, m4_previous, m4_date = _latest(mp2, "M4_GROWTH_MO") if mp2 is not None else (None, None, None)
    notes, notes_previous, notes_date = _latest(mp2, "NOTES_COINS_GROWTH_MO") if mp2 is not None else (None, None, None)
    if m4 is not None or notes is not None:
        directions = []
        if m4 is not None and m4_previous is not None: directions.append(m4 > m4_previous + CHANGE_EPSILON)
        if notes is not None and notes_previous is not None: directions.append(notes > notes_previous + CHANGE_EPSILON)
        direction = "positive" if directions and all(directions) else "negative" if directions and not any(directions) else "neutral"
        text = []
        if m4 is not None: text.append(f"M4 growth is {m4:.1f}%")
        if notes is not None: text.append(f"notes and coin growth is {notes:.1f}%")
        insights.append({"chart_id": "MP2", "headline": "Money and liquidity growth", "body": "; ".join(text) + ".", "direction": direction, "as_of_date": max(d for d in (m4_date, notes_date) if d is not None).date().isoformat()})

    mp3 = datasets.get("MP3")
    cost, _, cost_date = _latest(mp3, "CORP_OVERDRAFT_COST_MO") if mp3 is not None else (None, None, None)
    lending, _, lending_date = _latest(mp3, "NET_LENDING_CORP_MO") if mp3 is not None else (None, None, None)
    if cost is not None or lending is not None:
        text = []
        if cost is not None: text.append(f"corporate borrowing cost is {cost:.2f}%")
        if lending is not None: text.append(f"business-lending growth is {lending:.1f}%")
        direction = "negative" if lending is not None and lending < 0 else "positive" if lending is not None else "neutral"
        insights.append({"chart_id": "MP3", "headline": "Business credit transmission", "body": "; ".join(text) + ". These movements describe co-movement and do not establish causality.", "direction": direction, "as_of_date": max(d for d in (cost_date, lending_date) if d is not None).date().isoformat()})
    return insights
