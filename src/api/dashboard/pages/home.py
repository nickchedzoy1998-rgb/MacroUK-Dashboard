from typing import Any

import streamlit as st

from src.api.dashboard.components.home_components import (
    inject_home_styles,
    render_home_header,
    render_kpi_grid,
    render_macro_pulse_navigation,
    render_observation_note,
    render_section_heading,
    render_supporting_section,
)
from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json


def get_home_kpis(response: object) -> list[dict[str, Any]]:
    if (
        not response
        or not isinstance(response, dict)
        or "kpis" not in response
        or not isinstance(response["kpis"], list)
        or not response["kpis"]
    ):
        st.error(
            "Homepage data could not be loaded. FastAPI or the preparation "
            "pipeline may not be running."
        )
        st.stop()

    return response["kpis"]


endpoint = build_chart_endpoint("Home", "summary")
response = fetch_json(endpoint, False)
kpis = get_home_kpis(response)

inject_home_styles()

render_home_header()
render_section_heading("Headline indicators")
render_kpi_grid(kpis)
render_supporting_section()
render_macro_pulse_navigation()
render_observation_note()
