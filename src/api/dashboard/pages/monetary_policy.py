"""Streamlit orchestration for the Monetary Policy & Liquidity page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.api.dashboard.components.chart_components import build_business_credit_figure, build_money_supply_figure, build_policy_rates_figure, render_plotly_chart
from src.api.dashboard.components.shared_components import inject_dashboard_styles, render_analytical_page_header, render_chart_insight, render_chart_panel_header, render_data_freshness_note, render_empty_state, render_kpi_strip, render_methodology_note, render_page_summary, render_section_heading
from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json


BUILDERS = {"MP1": build_policy_rates_figure, "MP2": build_money_supply_figure, "MP3": build_business_credit_figure}
SUBTITLES = {"MP1": "Compare official policy and overnight market rates while keeping the gilt ETF as a separate price proxy.", "MP2": "Track broad money and notes-and-coin growth without assigning a single policy cause.", "MP3": "Compare corporate financing costs with business-lending growth; co-movement does not prove causality."}


def _valid(response: object) -> bool:
    if not isinstance(response, dict) or not isinstance(response.get("page"), dict) or not isinstance(response.get("kpis"), list) or not isinstance(response.get("charts"), list):
        return False
    return all(isinstance(chart, dict) and isinstance(chart.get("id"), str) and isinstance(chart.get("records"), list) and isinstance(chart.get("series_metadata"), list) and isinstance(chart.get("coverage"), dict) for chart in response["charts"])


def get_response() -> dict[str, Any]:
    try:
        response = fetch_json(build_chart_endpoint("MonetaryPolicy", "summary"), False)
    except Exception:
        st.error("Monetary Policy data could not be loaded. FastAPI or the preparation pipeline may not be running.")
        st.stop()
    if not _valid(response):
        st.error("Monetary Policy returned an invalid response and could not be displayed.")
        st.stop()
    return response


def render_chart(chart: dict[str, Any]) -> None:
    coverage = chart.get("coverage", {})
    latest = [value for value in coverage.get("latest_observation", {}).values() if value]
    note = f"Latest available {max(latest)}" if latest else ""
    optional_labels = {item["metric"]: item.get("label", item["metric"]) for item in chart.get("series_metadata", []) if item.get("optional")}
    missing = [optional_labels[item] for item in coverage.get("missing_metrics", []) if item in optional_labels]
    if missing:
        note += "; missing optional series: " + ", ".join(missing)
    with st.container(border=True):
        render_chart_panel_header(chart.get("title", chart["id"]), SUBTITLES.get(chart["id"], chart.get("description")))
        if note:
            render_data_freshness_note(note)
        if not chart.get("records"):
            render_empty_state("No prepared observations are available for this chart.")
        elif chart["id"] in BUILDERS:
            render_plotly_chart(BUILDERS[chart["id"]](chart), key=f"monetary-policy-{chart['id']}")
        if chart.get("insight"):
            render_chart_insight(chart["insight"].get("body"), label=chart["insight"].get("headline", "Insight"))


def render_page() -> None:
    inject_dashboard_styles()
    response = get_response()
    page = response["page"]
    render_analytical_page_header(page.get("title", "Monetary Policy & Liquidity"), page.get("description", ""), category="Monetary Policy")
    render_section_heading("Headline indicators")
    render_kpi_strip(response.get("kpis", []))
    render_page_summary(response.get("summary"), label="Current assessment")
    for chart in response["charts"]:
        render_chart(chart)
    render_methodology_note("Bank Rate and SONIA update daily, while money and credit series update monthly. The gilt series is an ETF price proxy rather than an official gilt yield; observation dates differ and the analysis is descriptive rather than financial advice.")


render_page()
