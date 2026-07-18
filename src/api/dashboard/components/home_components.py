from datetime import datetime
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import streamlit as st


def inject_home_styles() -> None:
    styles_path = Path(__file__).resolve().parents[1] / "styles" / "home.css"
    styles = styles_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)


def format_value(kpi: dict[str, Any], value_type: str) -> str | None:
    if value_type == "main":
        value = kpi["value"]
        unit = kpi["main_unit"]
    else:
        value = kpi["delta"]
        unit = kpi["delta_unit"]

    if value is None:
        return None

    if unit == "%":
        return f"{value:.1f}%"

    if unit == "pp":
        return f"{value:+.1f} pp"

    if unit == "index":
        return f"{value:,.0f}"

    return f"{value:,.1f}"


def format_date(date_value: str) -> str:
    parsed_date = datetime.fromisoformat(date_value)
    return parsed_date.strftime("%d %b %Y")


def get_delta_color(kpi: dict[str, Any]) -> str:
    delta = kpi.get("delta")
    if delta is None:
        return "neutral"

    delta_direction = (
        "inverse"
        if kpi.get("delta_direction") == "inverse"
        else "normal"
    )

    if delta == 0:
        return "neutral"

    is_positive = delta > 0
    is_favourable = is_positive if delta_direction == "normal" else not is_positive
    return "positive" if is_favourable else "negative"


def render_kpi_card(kpi: dict[str, Any]) -> str:
    value = format_value(kpi, "main") or "Not available"
    delta = format_value(kpi, "delta")
    delta_class = get_delta_color(kpi)
    delta_text = escape(delta) if delta else "&nbsp;"
    delta_label = escape("Change from previous observation") if delta else "&nbsp;"
    delta_missing_class = " home-kpi-card__delta--missing" if not delta else ""

    return (
        '<article class="home-kpi-card">'
        f'<div class="home-kpi-card__name">{escape(kpi["name"])}</div>'
        f'<div class="home-kpi-card__value">{escape(value)}</div>'
        f'<div class="home-kpi-card__delta home-kpi-card__delta--{delta_class}{delta_missing_class}">'
        f"<span>{delta_text}</span>"
        f"<small>{delta_label}</small>"
        "</div>"
        f'<p class="home-kpi-card__description">{escape(kpi["description"])}</p>'
        f'<div class="home-kpi-card__date">Latest observation: {escape(format_date(kpi["date"]))}</div>'
        "</article>"
    )


def render_kpi_grid(kpi_records: list[dict[str, Any]]) -> None:
    cards = "".join(render_kpi_card(kpi) for kpi in kpi_records)
    st.markdown(
        f'<section class="home-kpi-grid">{cards}</section>',
        unsafe_allow_html=True,
    )


def render_home_header() -> None:
    st.markdown(
        dedent("""
        <section class="home-title">
            <h1>MacroUK Dashboard</h1>
            <p>
                Track the health of the UK economy through growth, inflation,
                employment, monetary policy, housing, and financial markets.
            </p>
        </section>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_section_heading(title: str) -> None:
    st.markdown(
        dedent(f"""
        <div class="home-section-heading">
            <h2>{escape(title)}</h2>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_supporting_section() -> None:
    st.markdown(
        dedent("""
        <section class="home-supporting">
            <h3>How to use this dashboard</h3>
            <p>
                Start with the headline indicators to assess the current macro
                picture, then open Macro Pulse for a deeper view of trends,
                turning points, and supporting chart evidence.
            </p>
        </section>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_macro_pulse_navigation() -> None:
    if st.button("Go to MacroPulse Deep Dive"):
        st.switch_page("pages/macro_pulse.py")


def render_observation_note() -> None:
    st.markdown(
        dedent("""
        <p class="home-note">
            Observation dates vary across indicators because source datasets are
            released on different schedules.
        </p>
        """).strip(),
        unsafe_allow_html=True,
    )
