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


def render_plotly_chart(figure: Any, *, key: str | None = None, height: int | None = None) -> None:
    """Apply shared presentation defaults and render a prepared Plotly figure."""
    figure.update_layout(**DEFAULT_CHART_LAYOUT)
    if height is not None:
        figure.update_layout(height=height)
    st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG, key=key)
