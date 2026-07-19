"""Streamlit orchestration for Currency, Commodities and Fixed Income."""

from __future__ import annotations

import streamlit as st

from src.api.dashboard.components.chart_components import build_global_flows_figure, render_plotly_chart
from src.api.dashboard.components.shared_components import inject_dashboard_styles, render_analytical_page_header, render_chart_insight, render_chart_panel_header, render_data_freshness_note, render_empty_state, render_kpi_strip, render_methodology_note, render_page_summary, render_section_heading
from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json


def _valid(response: object) -> bool:
    return isinstance(response, dict) and isinstance(response.get("page"), dict) and isinstance(response.get("kpis"), list) and isinstance(response.get("charts"), list) and all(isinstance(chart, dict) and isinstance(chart.get("records"), list) and isinstance(chart.get("series_metadata"), list) and isinstance(chart.get("coverage"), dict) for chart in response["charts"])


def render_page() -> None:
    inject_dashboard_styles()
    try:
        response = fetch_json(build_chart_endpoint("GlobalFlows", "summary"), False)
    except Exception:
        st.error("Currency, Commodities and Fixed Income data could not be loaded. FastAPI or the preparation pipeline may not be running.")
        st.stop()
    if not _valid(response):
        st.error("Currency, Commodities and Fixed Income returned an invalid response and could not be displayed.")
        st.stop()
    page = response["page"]
    render_analytical_page_header(page.get("title", "Currency, Commodities & Fixed Income"), page.get("description", "Track sterling, market-price proxies and energy input prices."), category="Global Flows")
    render_section_heading("Headline indicators")
    render_kpi_strip(response.get("kpis", []))
    render_page_summary(response.get("summary"), label="Current assessment")
    for chart in response["charts"]:
        with st.container(border=True):
            render_chart_panel_header(chart.get("title", chart["id"]), chart.get("description"))
            latest = [value for value in chart.get("coverage", {}).get("latest_observation", {}).values() if value]
            text = []
            if chart.get("baseline_date"): text.append(f"Common baseline: {chart['baseline_date']}")
            if latest: text.append(f"Latest available {max(latest)}")
            optional_labels = {item["metric"]: item.get("label", item["metric"]) for item in chart.get("series_metadata", []) if item.get("optional")}
            missing = [optional_labels[item] for item in chart.get("coverage", {}).get("missing_metrics", []) if item in optional_labels]
            if missing: text.append("missing optional series: " + ", ".join(missing))
            if text: render_data_freshness_note(" · ".join(text))
            if not chart.get("records"): render_empty_state("No prepared observations are available for this chart.")
            else: render_plotly_chart(build_global_flows_figure(chart), key=f"global-flows-{chart['id']}")
            if chart.get("insight"): render_chart_insight(chart["insight"].get("body"), label=chart["insight"].get("headline", "Insight"))
    render_methodology_note("Sterling ERI and the BoE bilateral spot-rate alternatives are monthly. ETF series are price proxies rather than yields, gold and oil are quoted in USD, and observation dates vary. The analysis is descriptive rather than financial advice.")


render_page()
