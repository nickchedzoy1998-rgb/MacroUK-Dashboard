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


def render_economy_summary(summary: dict[str, Any] | None) -> None:
    if not summary:
        return

    headline = summary.get("headline")
    body = summary.get("body")
    if not headline or not body:
        return

    st.markdown(
        dedent(f"""
        <section class="home-summary-panel">
            <div class="home-eyebrow">UK economy at a glance</div>
            <h3>{escape(str(headline))}</h3>
            <p>{escape(str(body))}</p>
        </section>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_highlights(highlights: list[dict[str, Any]] | None) -> None:
    if not highlights:
        return

    cards = "".join(render_highlight_card(highlight) for highlight in highlights[:3])
    st.markdown(
        dedent(f"""
        <div class="home-section-heading home-section-heading--spaced">
            <h2>What changed?</h2>
        </div>
        <section class="home-highlight-grid">{cards}</section>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_highlight_card(highlight: dict[str, Any]) -> str:
    direction = highlight.get("direction", "neutral")
    if direction not in {"positive", "negative", "neutral"}:
        direction = "neutral"

    direction_label = {
        "positive": "Improving",
        "negative": "Watch",
        "neutral": "Stable",
    }[direction]

    return (
        f'<article class="home-highlight-card home-highlight-card--{direction}">'
        '<div class="home-highlight-card__meta">'
        f'<span class="home-highlight-card__marker">{escape(direction_label)}</span>'
        "</div>"
        f'<h3>{escape(str(highlight.get("title", "")))}</h3>'
        f'<p>{escape(str(highlight.get("text", "")))}</p>'
        "</article>"
    )


def render_dashboard_navigation() -> None:
    st.markdown(
        dedent("""
        <div class="home-section-heading home-section-heading--spaced">
            <h2>Explore the dashboard</h2>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    nav_items = [
        ("Macro Pulse", "Track growth, inflation and labour-market momentum.", "pages/macro_pulse.py", "Open Macro Pulse", "macro_pulse_nav"),
        ("Monetary Policy & Liquidity", "Follow policy rates, money growth and business credit.", "pages/monetary_policy.py", "Open Monetary Policy", "monetary_policy_nav"),
        ("Housing Market & Consumer Credit", "Track mortgage conditions, property activity and borrowing.", "pages/housing_credit.py", "Open Housing & Credit", "housing_credit_nav"),
        ("Financial Markets & Equities", "Compare UK equity tiers and selected company proxies.", "pages/financial_markets.py", "Open Financial Markets", "financial_markets_nav"),
        ("Currency, Commodities & Fixed Income", "Assess sterling, bond-asset proxies and energy prices.", "pages/global_flows.py", "Open Global Flows", "global_flows_nav"),
    ]

    for row_start in range(0, len(nav_items), 3):
        row_items = nav_items[row_start:row_start + 3]
        columns = st.columns(len(row_items))
        for column, item in zip(columns, row_items):
            title, description, page_path, action, key = item

            with column:
                with st.container(border=True):
                    st.markdown(
                        (
                            '<div class="home-nav-card">'
                            f"<h3>{escape(title)}</h3>"
                            f"<p>{escape(description)}</p>"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                    st.page_link(page_path, label=action)


def render_data_note() -> None:
    st.markdown(
        dedent("""
        <section class="home-data-note">
            <h3>About the data</h3>
            <p>
                Indicators update on different release schedules, so observation
                dates vary. Each card displays the latest available observation
                for that series. Headline values are drawn from official or
                established market sources, and the analysis is descriptive
                rather than financial advice.
            </p>
        </section>
        """).strip(),
        unsafe_allow_html=True,
    )
