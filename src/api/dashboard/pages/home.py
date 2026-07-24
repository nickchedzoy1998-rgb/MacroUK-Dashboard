from typing import Any

import streamlit as st

from src.api.dashboard.components.home_components import (
    inject_home_styles,
    render_dashboard_navigation,
    render_data_note,
    render_economy_summary,
    render_highlights,
    render_home_header,
    render_kpi_grid,
    render_section_heading,
)
from src.api.dashboard.data_loader import load_home_data


def stop_for_home_data_error() -> None:
    st.error(
        "Homepage data could not be loaded from the local warehouse."
    )
    st.stop()


def get_home_kpis(response: object) -> list[dict[str, Any]]:
    if (
        not response
        or not isinstance(response, dict)
        or "kpis" not in response
        or not isinstance(response["kpis"], list)
        or not response["kpis"]
    ):
        stop_for_home_data_error()

    return response["kpis"]


def get_optional_home_summary(response: object) -> dict[str, Any] | None:
    if not isinstance(response, dict):
        return None
    summary = response.get("summary")
    return summary if isinstance(summary, dict) else None


def get_optional_home_highlights(response: object) -> list[dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    highlights = response.get("highlights")
    return highlights if isinstance(highlights, list) else []


try:
    response = load_home_data()
except Exception:
    stop_for_home_data_error()

kpis = get_home_kpis(response)
summary = get_optional_home_summary(response)
highlights = get_optional_home_highlights(response)

inject_home_styles()

render_home_header()
render_section_heading("Headline indicators")
render_kpi_grid(kpis)
render_economy_summary(summary)
render_highlights(highlights)
render_dashboard_navigation()
render_data_note()
