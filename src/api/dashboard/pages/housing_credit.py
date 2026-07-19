"""Streamlit orchestration for Housing Market & Consumer Credit."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.api.dashboard.components.chart_components import build_buyer_composition_figure, build_household_borrowing_figure, build_mortgage_housing_figure, build_regional_housing_figure, render_plotly_chart
from src.api.dashboard.components.shared_components import inject_dashboard_styles, render_analytical_page_header, render_chart_insight, render_chart_panel_header, render_data_freshness_note, render_empty_state, render_kpi_strip, render_methodology_note, render_page_summary, render_section_heading
from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json

BUILDERS = {"HC1": build_mortgage_housing_figure, "HC2": build_regional_housing_figure, "HC3": build_buyer_composition_figure, "HC4": build_household_borrowing_figure}


def _valid(response: object) -> bool:
    return isinstance(response, dict) and isinstance(response.get("page"), dict) and isinstance(response.get("kpis"), list) and isinstance(response.get("charts"), list) and all(isinstance(chart, dict) and isinstance(chart.get("records"), list) and isinstance(chart.get("series_metadata"), list) and isinstance(chart.get("coverage"), dict) for chart in response["charts"])


def render_page() -> None:
    inject_dashboard_styles()
    try: response = fetch_json(build_chart_endpoint("HousingCredit", "summary"), False)
    except Exception: st.error("Housing and Consumer Credit data could not be loaded. FastAPI or the preparation pipeline may not be running."); st.stop()
    if not _valid(response): st.error("Housing and Consumer Credit returned an invalid response and could not be displayed."); st.stop()
    page = response["page"]; render_analytical_page_header(page["title"], page["description"], category="Housing & Credit"); render_section_heading("Headline indicators"); render_kpi_strip(response["kpis"]); render_page_summary(response.get("summary"), label="Current assessment")
    for chart in response["charts"]:
        with st.container(border=True):
            render_chart_panel_header(chart.get("title", chart["id"]), chart.get("description")); coverage = chart.get("coverage", {}); latest = [value for value in coverage.get("latest_observation", {}).values() if value]
            if chart.get("baseline_date"): render_data_freshness_note(f"Common baseline: {chart['baseline_date']}" + (f" · Latest available {max(latest)}" if latest else ""))
            elif latest: render_data_freshness_note(f"Latest available {max(latest)}")
            if not chart.get("records"): render_empty_state("No prepared observations are available for this chart.")
            else: render_plotly_chart(BUILDERS[chart["id"]](chart), key=f"housing-credit-{chart['id']}")
            if chart.get("geography"): st.caption(f"Geography: {chart['geography']}")
            if chart.get("insight"): render_chart_insight(chart["insight"].get("body"), label=chart["insight"].get("headline", "Insight"))
    render_methodology_note("Mortgage, credit and house-price data update monthly and official housing series may be revised. Regional and transaction geographies differ; HC3 uses England-and-Wales data where applicable. Observation dates vary and the analysis is descriptive rather than financial advice.")


render_page()
