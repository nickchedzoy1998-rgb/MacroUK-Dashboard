"""Shared Plotly builders and visual conventions for analytical pages."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


PLOTLY_CONFIG: dict[str, Any] = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

CHART_PALETTE = [
    "#2f6690",
    "#b45f43",
    "#6f7d3c",
    "#8a5a44",
    "#7a6c5d",
    "#6b6f9c",
    "#b08d2f",
]

_BASE_STYLE: dict[str, Any] = {
    "width": 2.2,
    "dash": "solid",
    "shape": "linear",
    "smoothing": 0.0,
    "opacity": 1.0,
}

SERIES_STYLES: dict[str, dict[str, Any]] = {
    "GDP_QOQ": {"color": "#2f6690", "width": 1.0, "opacity": 0.78},
    "GDP_YOY": {"color": "#b45f43", "width": 2.4, "shape": "linear"},
    "CPI": {"color": "#2f6690", "shape": "spline", "smoothing": 0.5},
    "CORE_CPI": {"color": "#b45f43", "shape": "spline", "smoothing": 0.5},
    "HOUSE_PRICE_GROWTH": {"color": "#6f7d3c", "shape": "spline", "smoothing": 0.45},
    "UNRATE": {"color": "#b45f43", "shape": "spline", "smoothing": 0.45},
    "EMPRATE": {"color": "#2f6690", "shape": "spline", "smoothing": 0.45},
    "WAGE_GROWTH": {"color": "#6f7d3c", "shape": "spline", "smoothing": 0.45},
    "BANK_RATE_DA": {"color": "#2f6690", "width": 2.6, "shape": "hv"},
    "SONIA": {"color": "#b45f43", "width": 2.1, "shape": "linear"},
    "BANK_RATE_SONIA_SPREAD": {"color": "#7a6c5d", "width": 1.7, "dash": "dot"},
    "ETF_UK_GILT_close": {"color": "#6f7d3c", "shape": "spline", "smoothing": 0.35},
    "M4_GROWTH_MO": {"color": "#2f6690", "shape": "spline", "smoothing": 0.45},
    "NOTES_COINS_GROWTH_MO": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.45},
    "CORP_OVERDRAFT_COST_MO": {"color": "#334e68", "width": 2.4, "shape": "spline", "smoothing": 0.35},
    "NET_LENDING_CORP_MO": {"color": "#b45f43", "opacity": 0.60},
    "MORTGAGE_2YR_75LTV_MO": {"color": "#2f6690", "shape": "spline", "smoothing": 0.4},
    "UK_HPI_YOY_CHANGE_UK": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.4},
    "UK_HPI_AVG_PRICE_UK_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.4},
    "UK_HPI_AVG_PRICE_LONDON_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.4},
    "UK_HPI_AVG_PRICE_NW_normalised": {"color": "#6f7d3c", "dash": "dot", "shape": "spline", "smoothing": 0.4},
    "UK_HPI_CASH_SALES_VOL": {"color": "#8a5a44", "opacity": 0.72},
    "UK_HPI_MORTGAGE_SALES_VOL": {"color": "#2f6690", "opacity": 0.72},
    "EW_TOTAL_TRANSACTIONS": {"color": "#6f7d3c", "width": 2.3},
    "NET_LENDING_DWELLINGS_MO": {"color": "#2f6690", "shape": "spline", "smoothing": 0.35},
    "NET_CONSUMER_CREDIT_MO": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.35},
    "FTSE_100_close_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.35},
    "FTSE_250_close_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.35},
    "FTSE_AIM_close_normalised": {"color": "#6f7d3c", "dash": "dot", "shape": "spline", "smoothing": 0.35},
    "EQ_TW_close_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.35},
    "EQ_BAR_close_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.35},
    "UK_HPI_INDEX_UK_normalised": {"color": "#6f7d3c", "dash": "dot", "shape": "spline", "smoothing": 0.35},
    "EQ_BARC_close_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.3},
    "EQ_BP_close_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.3},
    "EQ_RIO_close_normalised": {"color": "#6f7d3c", "dash": "dot", "shape": "spline", "smoothing": 0.3},
    "EQ_GSK_close_normalised": {"color": "#6b6f9c", "dash": "dashdot", "shape": "spline", "smoothing": 0.3},
    "SGE_L_close_normalised": {"color": "#b08d2f", "shape": "spline", "smoothing": 0.3},
    "STERLING_ERI_MO_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.4},
    "USD_GBP_SPOT_MO_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.4},
    "EUR_GBP_SPOT_MO_normalised": {"color": "#6f7d3c", "dash": "dot", "shape": "spline", "smoothing": 0.4},
    "ETF_UK_GILT_close_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.35},
    "ETF_UK_TIPS_close_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.35},
    "COM_GOLD_close_normalised": {"color": "#b08d2f", "dash": "dot", "shape": "spline", "smoothing": 0.35},
    "COM_OIL_BRENT_close_normalised": {"color": "#2f6690", "shape": "spline", "smoothing": 0.35},
    "COM_OIL_WTI_close_normalised": {"color": "#b45f43", "dash": "dash", "shape": "spline", "smoothing": 0.35},
}

# Backwards-compatible colour map for callers that only need the explicit colour.
SERIES_COLORS = {metric: style["color"] for metric, style in SERIES_STYLES.items()}

_LEGEND = {
    "orientation": "h",
    "yanchor": "bottom",
    "y": 1.02,
    "xanchor": "left",
    "x": 0,
    "font": {"size": 11},
    "itemsizing": "constant",
}

LAYOUT_PRESETS: dict[str, dict[str, Any]] = {
    "standard": {"height": 390, "margin": {"l": 55, "r": 45, "t": 58, "b": 88}, "legend": _LEGEND},
    "dense": {"height": 410, "margin": {"l": 55, "r": 45, "t": 68, "b": 90}, "legend": _LEGEND},
    "dual_axis": {"height": 420, "margin": {"l": 58, "r": 78, "t": 62, "b": 90}, "legend": _LEGEND},
    "subplots": {"height": 500, "margin": {"l": 58, "r": 55, "t": 78, "b": 92}, "legend": {**_LEGEND, "y": 1.08}},
    "financial": {"height": 450, "margin": {"l": 58, "r": 50, "t": 65, "b": 90}, "legend": _LEGEND},
}

DEFAULT_CHART_LAYOUT: dict[str, Any] = {
    "autosize": True,
    "hovermode": "x unified",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    **LAYOUT_PRESETS["standard"],
}

RANGE_SELECTOR = {
    "buttons": [
        {"count": 5, "label": "5Y", "step": "year", "stepmode": "backward"},
        {"count": 10, "label": "10Y", "step": "year", "stepmode": "backward"},
        {"count": 20, "label": "20Y", "step": "year", "stepmode": "backward"},
        {"step": "all", "label": "All"},
    ],
    "font": {"size": 10},
    "x": 0,
    "xanchor": "left",
    "y": -0.20,
    "yanchor": "top",
    "bgcolor": "rgba(255,255,255,0.98)",
    "activecolor": "rgba(47,102,144,0.20)",
    "bordercolor": "rgba(49,51,63,0.20)",
    "borderwidth": 1,
}

SECTOR_VIEW_MODES = ("Comparable growth", "Log scale", "Absolute rebased level")
DEFAULT_SECTOR_VIEW = SECTOR_VIEW_MODES[0]


def resolve_series_style(metric: str, fallback_index: int | None = None) -> dict[str, Any]:
    """Return a complete deterministic style for one metric."""
    style = dict(_BASE_STYLE)
    explicit = SERIES_STYLES.get(metric)
    if explicit:
        style.update(explicit)
        return style
    if fallback_index is None:
        digest = sha256(metric.encode("utf-8")).digest()
        fallback_index = int.from_bytes(digest[:2], "big") % len(CHART_PALETTE)
    style["color"] = CHART_PALETTE[fallback_index % len(CHART_PALETTE)]
    style["dash"] = ("solid", "dash", "dot", "dashdot")[
        (fallback_index // len(CHART_PALETTE)) % 4
    ]
    return style


def resolve_series_styles(metrics: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Resolve a chart's styles without reusing fallback colours until necessary."""
    ordered = list(dict.fromkeys(metrics))
    result: dict[str, dict[str, Any]] = {}
    used_fallback_colours: set[str] = set()
    for metric in ordered:
        if metric in SERIES_STYLES:
            result[metric] = resolve_series_style(metric)
            continue
        preferred = int.from_bytes(sha256(metric.encode("utf-8")).digest()[:2], "big") % len(CHART_PALETTE)
        available = [
            index for index, colour in enumerate(CHART_PALETTE)
            if colour not in used_fallback_colours
        ]
        fallback_index = min(available, key=lambda index: (index - preferred) % len(CHART_PALETTE)) if available else preferred
        result[metric] = resolve_series_style(metric, fallback_index)
        used_fallback_colours.add(result[metric]["color"])
    return result


def apply_chart_layout(figure: go.Figure, preset: str = "standard") -> go.Figure:
    """Apply a reusable layout preset without discarding builder-specific settings."""
    layout = {
        "autosize": True,
        "hovermode": "x unified",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        **deepcopy(LAYOUT_PRESETS[preset]),
    }
    figure.update_layout(**layout)
    return figure


def chart_frame(chart: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    """Convert API records to a sorted plotting frame and metadata map."""
    metadata = {item["metric"]: item for item in chart.get("series_metadata", [])}
    rows = []
    for record in chart.get("records", []):
        row = {"date": record.get("date")}
        row.update(record.get("values", {}))
        rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["date", *metadata]), metadata
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    numeric_columns = set(metadata)
    for metric in metadata:
        raw_metric = metric.removesuffix("_normalised")
        if raw_metric in frame:
            numeric_columns.add(raw_metric)
    for metric in numeric_columns:
        if metric not in frame:
            frame[metric] = pd.NA
        frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    return frame.dropna(subset=["date"]).sort_values("date").reset_index(drop=True), metadata


def _series_frame(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Drop only this trace's missing values, preserving sparse native frequency."""
    if metric not in frame:
        return pd.DataFrame(columns=["date", metric])
    return frame[["date", metric]].dropna(subset=[metric])


def _hover_template(label: str, unit: str) -> str:
    suffix = "%" if unit == "%" else f" {unit}" if unit else ""
    return f"%{{x|%d %b %Y}}<br>{label}: %{{y:.1f}}{suffix}<extra></extra>"


def _line(style: Mapping[str, Any]) -> dict[str, Any]:
    line = {
        "color": style["color"],
        "width": style["width"],
        "dash": style["dash"],
        "shape": style["shape"],
    }
    if style["shape"] == "spline":
        line["smoothing"] = style["smoothing"]
    return line


def _date_axis(
    figure: go.Figure,
    frame: pd.DataFrame,
    years: int,
    *,
    selector: bool = True,
    selector_row: int | None = None,
) -> None:
    kwargs: dict[str, Any] = {"type": "date", "showgrid": False, "nticks": 8}
    dates = frame.get("date")
    if dates is not None and dates.notna().any():
        latest = dates.max()
        earliest = dates.min()
        proposed = latest - pd.DateOffset(years=years)
        if proposed > earliest:
            kwargs["range"] = [proposed, latest]
    figure.update_xaxes(**kwargs)
    if selector:
        if selector_row is None:
            figure.update_xaxes(rangeselector=deepcopy(RANGE_SELECTOR))
        else:
            figure.update_xaxes(rangeselector=deepcopy(RANGE_SELECTOR), row=selector_row, col=1)


def build_growth_momentum_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        label = item["label"]
        if item.get("role") == "bar":
            figure.add_trace(go.Bar(
                x=series["date"], y=series[metric], name=label,
                marker={"color": styles[metric]["color"], "line": {"width": 0}},
                opacity=styles[metric]["opacity"],
                hovertemplate=_hover_template(label, item.get("unit", "")),
            ))
        else:
            figure.add_trace(go.Scatter(
                x=series["date"], y=series[metric], name=label, mode="lines",
                line=_line(styles[metric]), connectgaps=False,
                hovertemplate=_hover_template(label, item.get("unit", "")),
            ))
    figure.add_hline(y=float(chart.get("zero_reference", 0)), line_color="rgba(31,41,51,0.42)", line_width=1, line_dash="dot")
    figure.update_layout(barmode="group")
    figure.update_yaxes(title_text="Growth rate", ticksuffix="%", zeroline=False)
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "dual_axis")


def build_inflation_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), connectgaps=False,
            hovertemplate=_hover_template(item["label"], item.get("unit", "")),
        ))
    if chart.get("target") is not None:
        figure.add_hline(
            y=float(chart["target"]), line_color="#7a6c5d", line_width=1.1,
            line_dash="dash", annotation_text=f"{chart['target']:.0f}% target",
            annotation_position="bottom right",
        )
    figure.update_yaxes(title_text="Inflation rate", ticksuffix="%", zeroline=False)
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "dense")


def build_labour_market_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16,
        row_heights=[0.58, 0.42],
        subplot_titles=("Employment and unemployment rates", "Wage growth"),
    )
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        row = 2 if metric == "WAGE_GROWTH" else 1
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), connectgaps=False,
            hovertemplate=_hover_template(item["label"], item.get("unit", "")),
        ), row=row, col=1)
    figure.update_yaxes(title_text="Rate", ticksuffix="%", zeroline=False, row=1, col=1)
    figure.update_yaxes(title_text="Growth", ticksuffix="%", zeroline=False, row=2, col=1)
    _date_axis(figure, frame, 5, selector_row=2)
    return apply_chart_layout(figure, "subplots")


def build_policy_rates_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    has_spread = "BANK_RATE_SONIA_SPREAD" in metadata and not _series_frame(frame, "BANK_RATE_SONIA_SPREAD").empty
    has_proxy = any(item.get("role") == "price_proxy" for item in metadata.values())
    rows = 3 if has_spread and has_proxy else 2
    titles = ("Bank Rate and SONIA", "Bank Rate-SONIA spread", "UK gilt ETF price proxy") if rows == 3 else ("Bank Rate and SONIA", "UK gilt ETF price proxy" if has_proxy else "Bank Rate-SONIA spread")
    heights = [0.53, 0.18, 0.29] if rows == 3 else [0.65, 0.35]
    figure = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.10,
        row_heights=heights, subplot_titles=titles,
    )
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        if item.get("role") == "price_proxy":
            row = rows
        elif metric == "BANK_RATE_SONIA_SPREAD":
            row = 2
        else:
            row = 1
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), opacity=styles[metric]["opacity"],
            connectgaps=False, hovertemplate=_hover_template(item["label"], item.get("unit", "")),
        ), row=row, col=1)
    figure.update_yaxes(title_text="Rate", ticksuffix="%", row=1, col=1)
    if has_spread:
        figure.update_yaxes(title_text="pp", row=2, col=1)
        figure.add_hline(y=0, line_color="rgba(31,41,51,0.35)", line_dash="dot", row=2, col=1)
    if has_proxy:
        figure.update_yaxes(title_text="GBP price", row=rows, col=1)
    _date_axis(figure, frame, 5, selector_row=rows)
    return apply_chart_layout(figure, "subplots")


def build_money_supply_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), connectgaps=False,
            hovertemplate=_hover_template(item["label"], item.get("unit", "")),
        ))
    figure.add_hline(y=0, line_color="rgba(31,41,51,0.42)", line_dash="dot")
    figure.update_yaxes(title_text="Annual growth", ticksuffix="%", zeroline=False)
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "standard")


def build_business_credit_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        style = styles[metric]
        is_bar = item.get("role") == "bar"
        if is_bar:
            trace: go.BaseTraceType = go.Bar(
                x=series["date"], y=series[metric], name=item["label"],
                marker={"color": style["color"], "line": {"width": 0}},
                opacity=style["opacity"],
                hovertemplate=_hover_template(item["label"], item.get("unit", "")),
            )
        else:
            trace = go.Scatter(
                x=series["date"], y=series[metric], name=item["label"], mode="lines",
                line=_line(style), connectgaps=False,
                hovertemplate=_hover_template(item["label"], item.get("unit", "")),
            )
        figure.add_trace(trace, secondary_y=item.get("axis") == "right")
    figure.add_hline(y=0, line_color="rgba(31,41,51,0.42)", line_dash="dot", secondary_y=True)
    figure.update_yaxes(title_text="Borrowing cost", ticksuffix="%", secondary_y=False)
    figure.update_yaxes(title_text="Business-lending growth", ticksuffix="%", secondary_y=True)
    _date_axis(figure, frame, 5)
    figure.update_layout(barmode="relative")
    return apply_chart_layout(figure, "dual_axis")


def build_mortgage_housing_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), connectgaps=False,
            hovertemplate=_hover_template(item["label"], item.get("unit", "")),
        ), secondary_y=item.get("axis") == "right")
    figure.update_yaxes(title_text="Mortgage rate", ticksuffix="%", secondary_y=False)
    figure.update_yaxes(title_text="House-price growth", ticksuffix="%", secondary_y=True)
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "dual_axis")


def build_regional_housing_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), connectgaps=False,
            hovertemplate=f"%{{x|%d %b %Y}}<br>{item['label']}: %{{y:.1f}}<extra></extra>",
        ))
    figure.update_yaxes(title_text="Rebased index (baseline = 100)")
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "financial")


def build_buyer_composition_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        style = styles[metric]
        if item.get("role") == "line":
            figure.add_trace(go.Scatter(
                x=series["date"], y=series[metric], name=item["label"], mode="lines",
                line=_line(style), connectgaps=False,
                hovertemplate=_hover_template(item["label"], item.get("unit", "")),
            ))
        else:
            figure.add_trace(go.Bar(
                x=series["date"], y=series[metric], name=item["label"],
                marker={"color": style["color"], "line": {"width": 0}},
                opacity=style["opacity"],
                hovertemplate=_hover_template(item["label"], item.get("unit", "")),
            ))
    figure.update_layout(barmode="stack")
    figure.update_yaxes(title_text="Transactions")
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "financial")


def build_household_borrowing_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), connectgaps=False,
            hovertemplate=_hover_template(item["label"], item.get("unit", "")),
        ))
    figure.add_hline(y=0, line_dash="dot", line_color="rgba(31,41,51,0.42)")
    figure.update_yaxes(title_text="GBP millions")
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "standard")


def _market_customdata(frame: pd.DataFrame, series: pd.DataFrame, metric: str) -> Sequence[Any] | None:
    raw_metric = metric.removesuffix("_normalised")
    if raw_metric not in frame:
        return None
    return frame.set_index("date").reindex(series["date"])[raw_metric].to_numpy()


def build_financial_markets_figure(
    chart: dict[str, Any],
    view_mode: str | None = None,
) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    mode = view_mode or (DEFAULT_SECTOR_VIEW if chart.get("id") == "FM3" else "Absolute rebased level")
    if mode not in SECTOR_VIEW_MODES:
        raise ValueError(f"Unsupported sector comparison view: {mode}")
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        label = item["label"].replace(" (rebased)", "") if mode == "Comparable growth" else item["label"]
        rebased = series[metric].astype(float)
        valid = rebased.gt(0) if mode in {"Comparable growth", "Log scale"} else pd.Series(True, index=series.index)
        series = series.loc[valid].copy()
        rebased = rebased.loc[valid]
        if series.empty:
            continue
        raw = _market_customdata(frame, series, metric)
        if mode == "Comparable growth":
            plotted = 100.0 * np.log(rebased / 100.0)
            customdata = list(zip(rebased, raw if raw is not None else [None] * len(series)))
            hover = (
                f"%{{x|%d %b %Y}}<br>{label}: %{{y:.1f}}% log return"
                "<br>Rebased level: %{customdata[0]:.1f}"
                "<br>Original close: %{customdata[1]:.2f}<extra></extra>"
            )
        else:
            plotted = rebased
            customdata = raw
            hover = (
                f"%{{x|%d %b %Y}}<br>{label}: %{{y:.1f}}"
                + ("<br>Original close: %{customdata:.2f}" if raw is not None else "")
                + "<extra></extra>"
            )
        figure.add_trace(go.Scatter(
            x=series["date"], y=plotted, name=label, mode="lines",
            line=_line(styles[metric]), customdata=customdata,
            connectgaps=False, hovertemplate=hover,
        ))
    if mode == "Comparable growth":
        figure.add_hline(y=0, line_color="rgba(31,41,51,0.42)", line_dash="dot", annotation_text="Common baseline")
        figure.update_yaxes(title_text="Cumulative log return (%)", type="linear")
    else:
        figure.add_hline(y=100, line_color="rgba(31,41,51,0.42)", line_dash="dot", annotation_text="Common baseline = 100")
        figure.update_yaxes(
            title_text="Rebased index (baseline = 100)" + (" - logarithmic scale" if mode == "Log scale" else ""),
            type="log" if mode == "Log scale" else "linear",
        )
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "financial")


def build_global_flows_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    styles = resolve_series_styles(metadata)
    figure = go.Figure()
    for metric, item in metadata.items():
        series = _series_frame(frame, metric)
        if series.empty:
            continue
        raw = _market_customdata(frame, series, metric)
        hover = (
            f"%{{x|%d %b %Y}}<br>{item['label']}: %{{y:.1f}}"
            + ("<br>Original price/rate: %{customdata:.2f}" if raw is not None else "")
            + "<extra></extra>"
        )
        figure.add_trace(go.Scatter(
            x=series["date"], y=series[metric], name=item["label"], mode="lines",
            line=_line(styles[metric]), customdata=raw, connectgaps=False, hovertemplate=hover,
        ))
    figure.add_hline(y=100, line_color="rgba(31,41,51,0.42)", line_dash="dot", annotation_text="Common baseline = 100")
    figure.update_yaxes(title_text="Rebased index (baseline = 100)")
    _date_axis(figure, frame, 5)
    return apply_chart_layout(figure, "financial")


def render_plotly_chart(figure: Any, *, key: str | None = None, height: int | None = None) -> None:
    """Render a prepared Plotly figure using responsive shared controls."""
    if height is not None:
        figure.update_layout(height=height)
    st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG, key=key)
