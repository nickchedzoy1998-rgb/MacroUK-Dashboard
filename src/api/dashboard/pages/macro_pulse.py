"""Streamlit orchestration for the Macro Pulse analytical page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.api.dashboard.components.chart_components import (
    build_growth_momentum_figure,
    build_inflation_figure,
    build_labour_market_figure,
    render_plotly_chart,
)
from src.api.dashboard.components.shared_components import (
    inject_dashboard_styles,
    render_analytical_page_header,
    render_chart_insight,
    render_chart_panel_header,
    render_data_freshness_note,
    render_empty_state,
    render_kpi_strip,
    render_methodology_note,
    render_page_summary,
    render_section_heading,
)
from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json


CHART_BUILDERS = {
    "EGM": build_growth_momentum_figure,
    "IB": build_inflation_figure,
    "LBH": build_labour_market_figure,
}

CHART_SUBTITLES = {
    "EGM": "Compare short-term quarterly growth with the broader annual trend.",
    "IB": "Track headline and underlying price growth against the inflation target.",
    "LBH": "Assess employment conditions alongside the pace of wage growth.",
}


def stop_for_api_error(message: str) -> None:
    st.error(message)
    st.stop()


def get_macro_pulse_response() -> dict[str, Any]:
    endpoint = build_chart_endpoint("MacroPulse", "summary")
    try:
        response = fetch_json(endpoint, False)
    except Exception:
        stop_for_api_error(
            "Macro Pulse data could not be loaded. FastAPI or the preparation pipeline may not be running."
        )

    if not _valid_response(response):
        stop_for_api_error("Macro Pulse returned an invalid response and could not be displayed.")
    return response


def _valid_response(response: object) -> bool:
    if not isinstance(response, dict):
        return False
    if not isinstance(response.get("page"), dict):
        return False
    if not isinstance(response.get("kpis"), list):
        return False
    charts = response.get("charts")
    if not isinstance(charts, list) or not charts:
        return False
    for chart in charts:
        if not isinstance(chart, dict):
            return False
        if not isinstance(chart.get("id"), str):
            return False
        if not isinstance(chart.get("records"), list):
            return False
        if not isinstance(chart.get("series_metadata"), list):
            return False
        if not isinstance(chart.get("coverage"), dict):
            return False
    return True


def _chart_metadata_text(chart: dict[str, Any]) -> str:
    coverage = chart.get("coverage", {})
    latest = [value for value in coverage.get("latest_observation", {}).values() if value]
    first = [value for value in coverage.get("first_observation", {}).values() if value]
    parts = []
    if first:
        parts.append(f"Coverage from {min(first)}")
    if latest:
        parts.append(f"latest available {max(latest)}")

    optional_by_metric = {
        item.get("metric"): item.get("label", item.get("metric"))
        for item in chart.get("series_metadata", [])
        if item.get("optional")
    }
    missing = [optional_by_metric[metric] for metric in coverage.get("missing_metrics", []) if metric in optional_by_metric]
    if missing:
        parts.append("missing optional series: " + ", ".join(missing))
    return " · ".join(parts)


def render_chart(chart: dict[str, Any]) -> None:
    chart_id = chart["id"]
    title = chart.get("title", chart_id)
    subtitle = CHART_SUBTITLES.get(chart_id, chart.get("description"))
    with st.container(border=True):
        render_chart_panel_header(title, subtitle)
        metadata_text = _chart_metadata_text(chart)
        if metadata_text:
            render_data_freshness_note(metadata_text)

        if not chart.get("records"):
            render_empty_state("No prepared observations are available for this chart.")
        else:
            builder = CHART_BUILDERS.get(chart_id)
            if builder is None:
                render_empty_state("This chart type is not available yet.")
            else:
                render_plotly_chart(builder(chart), key=f"macro-pulse-{chart_id}")

        insight = chart.get("insight")
        if insight:
            render_chart_insight(insight.get("body"), label=insight.get("headline", "Insight"))


def render_macro_pulse_page() -> None:
    inject_dashboard_styles()
    response = get_macro_pulse_response()
    page = response["page"]

    render_analytical_page_header(
        page.get("title", "Macro Pulse"),
        page.get("description", "Track the UK economy through growth, inflation and labour-market momentum."),
        category="Macro Pulse",
    )
    render_section_heading("Headline indicators")
    render_kpi_strip(response.get("kpis", []))
    render_page_summary(response.get("summary"), label="Current assessment")

    for chart in response["charts"]:
        render_chart(chart)

    render_methodology_note(
        "GDP updates quarterly, while inflation and labour indicators update monthly. "
        "Observation dates may differ between series; charts use the latest available "
        "prepared data. The analysis is descriptive rather than financial advice."
    )


render_macro_pulse_page()
