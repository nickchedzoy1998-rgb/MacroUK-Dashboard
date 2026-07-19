"""Shared Plotly display conventions for analytical dashboard pages."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


PLOTLY_CONFIG: dict[str, Any] = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

DEFAULT_CHART_LAYOUT: dict[str, Any] = {
    "autosize": True,
    "hovermode": "x unified",
    "margin": {"l": 48, "r": 20, "t": 24, "b": 44},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "legend": {"orientation": "h", "y": 1.08, "x": 0},
}

SERIES_COLORS = {
    "GDP_QOQ": "#2f6690",
    "GDP_YOY": "#8a5a44",
    "CPI": "#2f6690",
    "CORE_CPI": "#8a5a44",
    "HOUSE_PRICE_GROWTH": "#6f7d3c",
    "UNRATE": "#b45f43",
    "EMPRATE": "#2f6690",
    "WAGE_GROWTH": "#6f7d3c",
    "FTSE_100_close_normalised": "#2f6690",
    "FTSE_250_close_normalised": "#8a5a44",
    "FTSE_AIM_close_normalised": "#6f7d3c",
    "EQ_TW_close_normalised": "#2f6690",
    "EQ_BAR_close_normalised": "#8a5a44",
    "UK_HPI_INDEX_UK_normalised": "#6f7d3c",
    "EQ_BARC_close_normalised": "#2f6690",
    "EQ_BP_close_normalised": "#8a5a44",
    "EQ_RIO_close_normalised": "#6f7d3c",
    "EQ_GSK_close_normalised": "#b45f43",
    "SGE_L_close_normalised": "#7a6c5d",
    "STERLING_ERI_MO_normalised": "#2f6690",
    "USD_GBP_SPOT_MO_normalised": "#8a5a44",
    "EUR_GBP_SPOT_MO_normalised": "#6f7d3c",
    "ETF_UK_GILT_close_normalised": "#2f6690",
    "ETF_UK_TIPS_close_normalised": "#8a5a44",
    "COM_GOLD_close_normalised": "#b08d2f",
    "COM_OIL_BRENT_close_normalised": "#2f6690",
    "COM_OIL_WTI_close_normalised": "#8a5a44",
}


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
    for metric in metadata:
        if metric not in frame:
            frame[metric] = pd.NA
        frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    return frame.dropna(subset=["date"]).sort_values("date").reset_index(drop=True), metadata


def _hover_template(label: str, unit: str) -> str:
    suffix = "%" if unit == "%" else f" {unit}" if unit else ""
    return f"%{{x|%d %b %Y}}<br>{label}: %{{y:.1f}}{suffix}<extra></extra>"


def build_growth_momentum_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        trace_kwargs = {
            "x": frame["date"],
            "y": frame[metric],
            "name": item["label"],
            "marker_color": SERIES_COLORS.get(metric, "#2f6690"),
            "hovertemplate": _hover_template(item["label"], item.get("unit", "")),
        }
        if item.get("role") == "bar":
            figure.add_trace(go.Bar(**trace_kwargs))
        else:
            figure.add_trace(
                go.Scatter(
                    **trace_kwargs,
                    mode="lines",
                    line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.2},
                    connectgaps=False,
                )
            )
    figure.add_hline(
        y=float(chart.get("zero_reference", 0)),
        line_color="rgba(31, 41, 51, 0.45)",
        line_width=1,
        line_dash="dot",
    )
    figure.update_layout(barmode="group", height=410)
    figure.update_yaxes(title_text="Percent", ticksuffix="%", zeroline=False)
    figure.update_xaxes(type="date", showgrid=False)
    return figure


def build_inflation_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        color = SERIES_COLORS.get(metric, "#2f6690")
        figure.add_trace(
            go.Scatter(
                x=frame["date"],
                y=frame[metric],
                name=item["label"],
                mode="lines",
                line={"color": color, "width": 2.1},
                connectgaps=False,
                hovertemplate=_hover_template(item["label"], item.get("unit", "")),
            )
        )
    if chart.get("target") is not None:
        figure.add_hline(
            y=float(chart["target"]),
            line_color="#6f7d3c",
            line_width=1.2,
            line_dash="dash",
            annotation_text=f"{chart['target']:.0f}% target",
            annotation_position="top left",
        )
    figure.update_layout(height=410)
    figure.update_yaxes(title_text="Percent", ticksuffix="%", zeroline=False)
    figure.update_xaxes(type="date", showgrid=False)
    return figure


def build_labour_market_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Employment rates", "Wage growth"),
    )
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        row = 2 if metric == "WAGE_GROWTH" else 1
        color = SERIES_COLORS.get(metric, "#2f6690")
        figure.add_trace(
            go.Scatter(
                x=frame["date"],
                y=frame[metric],
                name=item["label"],
                mode="lines",
                line={"color": color, "width": 2.1},
                connectgaps=False,
                hovertemplate=_hover_template(item["label"], item.get("unit", "")),
            ),
            row=row,
            col=1,
        )
    figure.update_yaxes(title_text="Percent", ticksuffix="%", zeroline=False, row=1, col=1)
    figure.update_yaxes(title_text="Percent", ticksuffix="%", zeroline=False, row=2, col=1)
    figure.update_xaxes(type="date", showgrid=False, row=2, col=1)
    figure.update_layout(height=500, showlegend=True)
    return figure


def build_policy_rates_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=("Bank Rate and SONIA (%)", "UK gilt ETF price proxy (GBP)"))
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        color = SERIES_COLORS.get(metric, "#2f6690")
        row = 2 if item.get("role") == "price_proxy" else 1
        figure.add_trace(go.Scatter(x=frame["date"], y=frame[metric], name=item["label"], mode="lines", line={"color": color, "width": 2.1, "shape": "hv" if metric == "BANK_RATE_DA" else "linear"}, connectgaps=False, hovertemplate=_hover_template(item["label"], item.get("unit", ""))), row=row, col=1)
    figure.update_yaxes(title_text="Percent", ticksuffix="%", row=1, col=1)
    figure.update_yaxes(title_text="GBP price", row=2, col=1)
    figure.update_xaxes(type="date", showgrid=False, row=2, col=1)
    figure.update_layout(height=520)
    return figure


def build_money_supply_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        figure.add_trace(go.Scatter(x=frame["date"], y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}, connectgaps=False, hovertemplate=_hover_template(item["label"], item.get("unit", ""))))
    figure.add_hline(y=0, line_color="rgba(31, 41, 51, 0.45)", line_dash="dot")
    figure.update_yaxes(title_text="Percent", ticksuffix="%", zeroline=False)
    figure.update_xaxes(type="date", showgrid=False)
    figure.update_layout(height=410)
    return figure


def build_business_credit_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        is_bar = item.get("role") == "bar"
        color = SERIES_COLORS.get(metric, "#2f6690")
        trace = go.Bar(x=frame["date"], y=frame[metric], name=item["label"], marker_color=color, hovertemplate=_hover_template(item["label"], item.get("unit", ""))) if is_bar else go.Scatter(x=frame["date"], y=frame[metric], name=item["label"], mode="lines", line={"color": color, "width": 2.1}, hovertemplate=_hover_template(item["label"], item.get("unit", "")))
        figure.add_trace(trace, secondary_y=item.get("axis") == "right")
    figure.add_hline(y=0, line_color="rgba(31, 41, 51, 0.45)", line_dash="dot", secondary_y=True)
    figure.update_yaxes(title_text="Borrowing cost (%)", ticksuffix="%", secondary_y=False)
    figure.update_yaxes(title_text="Business-lending growth (%)", ticksuffix="%", secondary_y=True)
    figure.update_xaxes(type="date", showgrid=False)
    figure.update_layout(height=430, barmode="relative")
    return figure


def build_mortgage_housing_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart); figure = make_subplots(specs=[[{"secondary_y": True}]])
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0: continue
        figure.add_trace(go.Scatter(x=frame.date, y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}, hovertemplate=_hover_template(item["label"], item.get("unit", ""))), secondary_y=item.get("axis") == "right")
    figure.update_yaxes(title_text="Mortgage rate (%)", ticksuffix="%", secondary_y=False); figure.update_yaxes(title_text="House-price growth (%)", ticksuffix="%", secondary_y=True); figure.update_xaxes(type="date", showgrid=False); figure.update_layout(height=420); return figure


def build_regional_housing_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart); figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0: continue
        figure.add_trace(go.Scatter(x=frame.date, y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}, hovertemplate=f"%{{x|%d %b %Y}}<br>{item['label']}: %{{y:.1f}}<extra></extra>"))
    figure.update_yaxes(title_text="Rebased index (common baseline = 100)"); figure.update_xaxes(type="date", showgrid=False); figure.update_layout(height=430); return figure


def build_buyer_composition_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart); figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0: continue
        if item.get("role") == "line": figure.add_trace(go.Scatter(x=frame.date, y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}))
        else: figure.add_trace(go.Bar(x=frame.date, y=frame[metric], name=item["label"], marker_color=SERIES_COLORS.get(metric, "#2f6690")))
    figure.update_layout(barmode="stack", height=430); figure.update_yaxes(title_text="Transactions"); figure.update_xaxes(type="date", showgrid=False); return figure


def build_household_borrowing_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart); figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0: continue
        figure.add_trace(go.Scatter(x=frame.date, y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}))
    figure.add_hline(y=0, line_dash="dot", line_color="rgba(31,41,51,0.45)"); figure.update_yaxes(title_text="GBP millions"); figure.update_xaxes(type="date", showgrid=False); figure.update_layout(height=430); return figure


def build_financial_markets_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        raw_metric = metric.removesuffix("_normalised")
        customdata = frame[raw_metric] if raw_metric in frame else None
        hover = f"%{{x|%d %b %Y}}<br>{item['label']}: %{{y:.1f}}<br>Original close: %{{customdata:.2f}}<extra></extra>" if customdata is not None else _hover_template(item["label"], item.get("unit", "Index"))
        figure.add_trace(go.Scatter(x=frame["date"], y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}, customdata=customdata, connectgaps=False, hovertemplate=hover))
    figure.add_hline(y=100, line_color="rgba(31, 41, 51, 0.45)", line_dash="dot", annotation_text="Common baseline = 100")
    figure.update_layout(height=430)
    figure.update_yaxes(title_text="Rebased index (common baseline = 100)")
    figure.update_xaxes(type="date", showgrid=False)
    return figure


def build_global_flows_figure(chart: dict[str, Any]) -> go.Figure:
    frame, metadata = chart_frame(chart)
    figure = go.Figure()
    for metric, item in metadata.items():
        if metric not in frame or frame[metric].notna().sum() == 0:
            continue
        raw_metric = metric.removesuffix("_normalised")
        customdata = frame[raw_metric] if raw_metric in frame else None
        hover = f"%{{x|%d %b %Y}}<br>{item['label']}: %{{y:.1f}}<br>Original price/rate: %{{customdata:.2f}}<extra></extra>" if customdata is not None else _hover_template(item["label"], item.get("unit", "Index"))
        figure.add_trace(go.Scatter(x=frame["date"], y=frame[metric], name=item["label"], mode="lines", line={"color": SERIES_COLORS.get(metric, "#2f6690"), "width": 2.1}, customdata=customdata, connectgaps=False, hovertemplate=hover))
    figure.add_hline(y=100, line_color="rgba(31, 41, 51, 0.45)", line_dash="dot", annotation_text="Common baseline = 100")
    figure.update_layout(height=430)
    figure.update_yaxes(title_text="Rebased index (common baseline = 100)")
    figure.update_xaxes(type="date", showgrid=False)
    return figure


def render_plotly_chart(figure: Any, *, key: str | None = None, height: int | None = None) -> None:
    """Apply shared presentation defaults and render a prepared Plotly figure."""
    figure.update_layout(**DEFAULT_CHART_LAYOUT)
    if height is not None:
        figure.update_layout(height=height)
    st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG, key=key)
