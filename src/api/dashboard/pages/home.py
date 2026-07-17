import streamlit as st
from datetime import datetime
from html import escape
from textwrap import dedent

from src.utilities.build_url import build_chart_endpoint
from src.utilities.http_client import fetch_json
from src.utilities.config_loader import load_config

# Helpers:
home_config = load_config('charts', 'Home')
home_kpis = list(home_config.keys())
endpoint = build_chart_endpoint('Home', 'summary')
response = fetch_json(endpoint, False)

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

kpis = response['kpis']


def format_value(kpi, value_type):
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


def format_date(date_value):
    parsed_date = datetime.fromisoformat(date_value)
    return parsed_date.strftime("%d %b %Y")


def get_delta_color(kpi):
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


def render_kpi_card(kpi):
    value = format_value(kpi, 'main') or "Not available"
    delta = format_value(kpi, 'delta')
    delta_class = get_delta_color(kpi)
    delta_text = escape(delta) if delta else "&nbsp;"
    delta_label = escape("Change from previous observation") if delta else "&nbsp;"
    delta_missing_class = " home-kpi-card__delta--missing" if not delta else ""

    return (
        '<article class="home-kpi-card">'
        f'<div class="home-kpi-card__name">{escape(kpi["name"])}</div>'
        f'<div class="home-kpi-card__value">{escape(value)}</div>'
        f'<div class="home-kpi-card__delta home-kpi-card__delta--{delta_class}{delta_missing_class}">'
        f'<span>{delta_text}</span>'
        f'<small>{delta_label}</small>'
        '</div>'
        f'<p class="home-kpi-card__description">{escape(kpi["description"])}</p>'
        f'<div class="home-kpi-card__date">Latest observation: {escape(format_date(kpi["date"]))}</div>'
        '</article>'
    )


def render_kpi_grid(kpi_records):
    cards = "".join(render_kpi_card(kpi) for kpi in kpi_records)
    return f'<section class="home-kpi-grid">{cards}</section>'


st.markdown(
    dedent("""
    <style>
    .home-title {
        background: linear-gradient(90deg, rgba(47, 102, 144, 0.08), rgba(22, 121, 76, 0.05));
        border: 1px solid rgba(49, 51, 63, 0.10);
        border-left: 4px solid #2f6690;
        border-radius: 8px;
        margin-bottom: 1.75rem;
        padding: 1.25rem 1.35rem;
    }

    .home-title h1 {
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 680;
        letter-spacing: 0;
        margin-bottom: 0.35rem;
    }

    .home-title p,
    .home-supporting p,
    .home-note {
        color: rgba(31, 41, 51, 0.74);
        font-size: 1rem;
        line-height: 1.55;
        margin: 0;
    }

    .home-section-heading {
        margin: 0.25rem 0 0.85rem;
    }

    .home-section-heading h2 {
        color: #1f2933;
        font-size: 1.35rem;
        font-weight: 650;
        letter-spacing: 0;
        margin: 0;
    }

    .home-kpi-grid {
        align-items: stretch;
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        margin: 0.25rem 0 1.75rem;
    }

    .home-kpi-card {
        background: linear-gradient(180deg, #ffffff, #fbfcfd);
        border: 1px solid rgba(49, 51, 63, 0.16);
        border-top: 3px solid #2f6690;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        min-height: 245px;
        padding: 1.15rem 1.2rem 1rem;
    }

    .home-kpi-card:nth-child(2) {
        border-top-color: #8a5a44;
    }

    .home-kpi-card:nth-child(3) {
        border-top-color: #5b6c8f;
    }

    .home-kpi-card:nth-child(4) {
        border-top-color: #6f7d3c;
    }

    .home-kpi-card:nth-child(5) {
        border-top-color: #9b6b2f;
    }

    .home-kpi-card:nth-child(6) {
        border-top-color: #5d6f78;
    }

    .home-kpi-card__name {
        color: rgba(31, 41, 51, 0.78);
        font-size: 0.86rem;
        font-weight: 650;
        line-height: 1.3;
        margin-bottom: 0.55rem;
    }

    .home-kpi-card__value {
        color: #1f2933;
        font-size: 2.1rem;
        font-weight: 720;
        letter-spacing: 0;
        line-height: 1.08;
        margin-bottom: 0.45rem;
    }

    .home-kpi-card__delta {
        align-items: baseline;
        display: flex;
        gap: 0.45rem;
        min-height: 1.45rem;
        margin-bottom: 0.85rem;
    }

    .home-kpi-card__delta span {
        font-size: 0.96rem;
        font-weight: 650;
    }

    .home-kpi-card__delta small {
        color: rgba(31, 41, 51, 0.56);
        font-size: 0.76rem;
        line-height: 1.2;
    }

    .home-kpi-card__delta--positive span {
        color: #16794c;
    }

    .home-kpi-card__delta--negative span {
        color: #b42318;
    }

    .home-kpi-card__delta--neutral span {
        color: rgba(31, 41, 51, 0.62);
    }

    .home-kpi-card__delta--missing {
        visibility: hidden;
    }

    .home-kpi-card__description {
        color: rgba(31, 41, 51, 0.70);
        font-size: 0.91rem;
        line-height: 1.45;
        margin: 0;
    }

    .home-kpi-card__date {
        border-top: 1px solid rgba(49, 51, 63, 0.10);
        color: rgba(31, 41, 51, 0.60);
        font-size: 0.78rem;
        margin-top: auto;
        padding-top: 0.8rem;
    }

    .home-supporting {
        background: rgba(47, 102, 144, 0.045);
        border: 1px solid rgba(47, 102, 144, 0.12);
        border-radius: 8px;
        margin-top: 0.8rem;
        padding: 1.05rem 1.15rem;
    }

    .home-supporting h3 {
        color: #1f2933;
        font-size: 1.05rem;
        font-weight: 650;
        letter-spacing: 0;
        margin: 0 0 0.35rem;
    }

    .home-note {
        font-size: 0.84rem;
        margin-top: 0.85rem;
    }

    div[data-testid="stButton"] > button {
        background: #2f6690;
        border-color: #2f6690;
        border-radius: 6px;
        color: #ffffff;
        font-weight: 600;
    }

    div[data-testid="stButton"] > button:hover {
        background: #28577b;
        border-color: #28577b;
        color: #ffffff;
    }

    @media (max-width: 900px) {
        .home-kpi-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 640px) {
        .home-kpi-grid {
            grid-template-columns: 1fr;
        }

        .home-kpi-card {
            min-height: 0;
        }
    }
    </style>
    """).strip(),
    unsafe_allow_html=True,
)


### DASHBOARD ###

st.markdown(
    dedent("""
    <section class="home-title">
        <h1>UK Economic Dashboard</h1>
        <p>
            Track the health of the UK economy through growth, inflation,
            employment, monetary policy, housing, and financial markets.
        </p>
    </section>
    """).strip(),
    unsafe_allow_html=True,
)

st.markdown(
    dedent("""
    <div class="home-section-heading">
        <h2>Headline indicators</h2>
    </div>
    """).strip(),
    unsafe_allow_html=True,
)

st.markdown(render_kpi_grid(kpis), unsafe_allow_html=True)

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

if st.button("Go to MacroPulse Deep Dive"):
    st.switch_page('pages/macro_pulse.py')

st.markdown(
    dedent("""
    <p class="home-note">
        Observation dates vary across indicators because source datasets are
        released on different schedules.
    </p>
    """).strip(),
    unsafe_allow_html=True,
)
