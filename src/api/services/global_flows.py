"""Deterministic interpretation rules for currency, commodities and fixed income."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.utilities.config_loader import load_config, resolve_metric_label


EPSILON = 0.05


def _latest(frame: pd.DataFrame | None, column: str) -> tuple[float | None, pd.Timestamp | None]:
    if frame is None or column not in frame.columns: return None, None
    rows = frame[["date", column]].copy(); rows[column] = pd.to_numeric(rows[column], errors="coerce"); rows = rows.dropna(subset=["date", column]).sort_values("date")
    return (None, None) if rows.empty else (float(rows.iloc[-1][column]), pd.Timestamp(rows.iloc[-1].date))


def _state(value: float | None) -> str:
    return "broadly stable" if value is None or abs(value) <= EPSILON else "strengthening" if value > 0 else "weakening"


def build_global_flows_summary(kpis: list[Mapping[str, Any]], gf1: pd.DataFrame | None = None, gf3: pd.DataFrame | None = None) -> dict[str, str]:
    mapped = {str(item.get("kpi_id")): item for item in kpis}; parts = []
    eri = mapped.get("STERLING_ERI", {}).get("value")
    usd = mapped.get("GBP_USD", {}).get("value")
    if eri is not None: parts.append(f"sterling ERI is {_state(float(eri))} over the latest month")
    if usd is not None: parts.append(f"GBP/USD is {_state(float(usd))} over the latest month")
    brent = mapped.get("BRENT", {}).get("value")
    if brent is not None: parts.append(f"Brent is {_state(float(brent))} over one month")
    headline = "Currency and market-flow indicators are not available."
    if parts:
        text = "; ".join(parts)
        headline = text[:1].upper() + text[1:] + "."
    return {"headline": headline, "body": "Exchange rates are shown in their source direction; ETF series are price proxies, not yields. Commodity prices are USD-denominated. The analysis is descriptive and does not constitute financial advice."}


def build_global_flows_insights(datasets: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    result = []
    gf1 = datasets.get("GF1")
    if gf1 is not None and not gf1.empty:
        row = gf1.iloc[-1]; eri = row.get("STERLING_ERI_MO_return_1m")
        result.append({"chart_id": "GF1", "headline": "Sterling direction", "body": f"Sterling ERI is {float(eri):.1f}% higher over the latest month." if pd.notna(eri) else "Sterling ERI is available; the latest monthly change is unavailable.", "direction": "positive" if pd.notna(eri) and eri > EPSILON else "negative" if pd.notna(eri) and eri < -EPSILON else "neutral", "as_of_date": pd.Timestamp(row.date).date().isoformat()})
    gf2 = datasets.get("GF2")
    if gf2 is not None:
        columns = [c for c in gf2.columns if c.endswith("_normalised")]
        valid = gf2.dropna(subset=columns) if columns else pd.DataFrame()
        if not valid.empty:
            labels = (load_config("charts", "GlobalFlows", "GF2") or {}).get("metric_labels", {})
            row = valid.iloc[-1]
            values = {c: float(row[c]) for c in columns}
            best = resolve_metric_label(max(values, key=values.get), labels)
            weakest = resolve_metric_label(min(values, key=values.get), labels)
            result.append({"chart_id": "GF2", "headline": "Fixed income and gold comparison", "body": f"{best} is highest and {weakest} lowest at the latest common rebased observation. Relative performance does not establish inflation expectations.", "direction": "neutral", "as_of_date": pd.Timestamp(row.date).date().isoformat()})
    gf3 = datasets.get("GF3")
    if gf3 is not None and not gf3.empty:
        row = gf3.iloc[-1]; brent = row.get("COM_OIL_BRENT_close_return_21d"); wti = row.get("COM_OIL_WTI_close_return_21d"); spread = row.get("BRENT_WTI_SPREAD")
        result.append({"chart_id": "GF3", "headline": "Energy input prices", "body": f"Brent is {float(brent):.1f}% and WTI {float(wti):.1f}% over one month; the latest Brent-minus-WTI spread is {float(spread):.2f} USD per barrel." if pd.notna(brent) and pd.notna(wti) and pd.notna(spread) else "Brent and WTI data is partially available; the comparison is incomplete.", "direction": "neutral", "as_of_date": pd.Timestamp(row.date).date().isoformat()})
    return result
