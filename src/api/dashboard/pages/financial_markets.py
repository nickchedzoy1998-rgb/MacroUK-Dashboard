"""Streamlit orchestration for Financial Markets and Equities."""

from __future__ import annotations

import streamlit as st

from src.api.dashboard.components.chart_components import (
    DEFAULT_SECTOR_VIEW,
    SECTOR_VIEW_MODES,
    build_financial_markets_figure,
    render_plotly_chart,
)
from src.api.dashboard.components.shared_components import inject_dashboard_styles, render_analytical_page_header, render_chart_insight, render_chart_panel_header, render_data_freshness_note, render_empty_state, render_kpi_strip, render_methodology_note, render_page_summary, render_section_heading
from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json


def _valid(response: object) -> bool:
    return isinstance(response, dict) and isinstance(response.get("page"), dict) and isinstance(response.get("kpis"), list) and isinstance(response.get("charts"), list) and all(isinstance(chart, dict) and isinstance(chart.get("records"), list) and isinstance(chart.get("series_metadata"), list) and isinstance(chart.get("coverage"), dict) for chart in response["charts"])


def render_page() -> None:
    inject_dashboard_styles()
    try:
        response = fetch_json(build_chart_endpoint("FinancialMarkets", "summary"), False)
    except Exception as exc:
        st.error(f"Financial Markets data could not be loaded: {exc}")
        st.stop()
    if not _valid(response):
        st.error("Financial Markets returned an invalid response and could not be displayed.")
        st.stop()
    page = response["page"]
    render_analytical_page_header(page.get("title", "Financial Markets & Equities"), page.get("description", "Track UK equity tiers and selected company proxies."), category="Financial Markets")
    render_section_heading("Headline indicators")
    render_kpi_strip(response.get("kpis", []))
    render_page_summary(response.get("summary"), label="Current assessment")
    for chart in response["charts"]:
        with st.container(border=True):
            render_chart_panel_header(chart.get("title", chart["id"]), chart.get("description"))
            coverage = chart.get("coverage", {})
            latest = [value for value in coverage.get("latest_observation", {}).values() if value]
            parts = []
            if chart.get("baseline_date"):
                parts.append(f"Common baseline: {chart['baseline_date']}")
            if latest:
                parts.append(f"Latest available {max(latest)}")
            if parts:
                render_data_freshness_note(" · ".join(parts))
            if not chart.get("records"):
                render_empty_state("No prepared observations are available for this chart.")
            else:
                view_mode = None
                if chart["id"] == "FM3":
                    view_mode = st.radio(
                        "Chart view",
                        SECTOR_VIEW_MODES,
                        index=SECTOR_VIEW_MODES.index(DEFAULT_SECTOR_VIEW),
                        horizontal=True,
                        key="financial-markets-fm3-view",
                        help=(
                            "Comparable growth shows cumulative log returns. Log scale and "
                            "absolute level retain the rebased index."
                        ),
                    )
                    if view_mode == "Absolute rebased level":
                        st.caption(
                            "Extreme long-run compounding can compress lower-growth series "
                            "in this view."
                        )
                render_plotly_chart(
                    build_financial_markets_figure(chart, view_mode=view_mode),
                    key=f"financial-markets-{chart['id']}-{view_mode or 'standard'}",
                )
            if chart.get("insight"):
                render_chart_insight(chart["insight"].get("body"), label=chart["insight"].get("headline", "Insight"))
    render_methodology_note("FM1 and FM3 use trading-day market observations. FM2 compares month-end housebuilder prices with the official monthly UK HPI index; the frequencies are not treated as identical. Sector Proxy Performance defaults to cumulative log return, calculated as 100 times the natural log of the rebased index divided by 100; this preserves relative growth comparison without capping genuine values. The other views retain the positive rebased level on logarithmic or linear axes. Company series are selected proxies rather than complete sector indices. Observation dates vary and the analysis is descriptive rather than investment advice.")


render_page()
