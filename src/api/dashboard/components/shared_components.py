"""Reusable presentation components for analytical Streamlit pages."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

import streamlit as st


def inject_dashboard_styles() -> None:
    """Load the shared analytical stylesheet independently of the CWD."""
    styles_path = Path(__file__).resolve().parents[1] / "styles" / "dashboard.css"
    styles = styles_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)


def render_analytical_page_header(
    title: str,
    description: str,
    *,
    category: str | None = None,
) -> None:
    eyebrow = f'<div class="dashboard-page-header__category">{escape(category)}</div>' if category else ""
    html = (
        '<section class="dashboard-page-header">'
        f"{eyebrow}<h1>{escape(title)}</h1><p>{escape(description)}</p>"
        "</section>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_section_heading(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<p>{escape(subtitle)}</p>' if subtitle else ""
    html = (
        '<div class="dashboard-section-heading">'
        f"<h2>{escape(title)}</h2>{subtitle_html}"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_strip(kpis: Sequence[Mapping[str, Any]]) -> None:
    """Render prepared KPI records without querying or transforming data."""
    cards: list[str] = []
    for kpi in kpis:
        value = kpi.get("value")
        value_display = _format_kpi_value(value, kpi.get("main_unit"))
        delta = kpi.get("delta")
        delta_display = _format_kpi_value(delta, kpi.get("delta_unit"), signed=True)
        delta_class = _kpi_delta_class(delta, kpi.get("delta_direction"))
        delta_html = (
            f'<div class="dashboard-kpi__delta dashboard-kpi__delta--{delta_class}">'
            f'{escape(delta_display)}</div>'
            if delta is not None
            else '<div class="dashboard-kpi__delta dashboard-kpi__delta--missing">&nbsp;</div>'
        )
        date = kpi.get("date") or kpi.get("latest_date")
        date_html = f'<div class="dashboard-kpi__date">Latest: {escape(str(date))}</div>' if date else ""
        cards.append(
            '<article class="dashboard-kpi">'
            f'<div class="dashboard-kpi__label">{escape(str(kpi.get("label", kpi.get("name", ""))))}</div>'
            f'<div class="dashboard-kpi__value">{escape(value_display)}</div>'
            f"{delta_html}"
            f'<p class="dashboard-kpi__description">{escape(str(kpi.get("description", "")))}</p>'
            f"{date_html}"
            "</article>"
        )
    html = '<section class="dashboard-kpi-strip">' + "".join(cards) + "</section>"
    st.markdown(html, unsafe_allow_html=True)


def _format_kpi_value(value: Any, unit: Any, *, signed: bool = False) -> str:
    if value is None:
        return "Not available"
    number = float(value)
    if unit == "%":
        return f"{number:+.1f}%" if signed else f"{number:.1f}%"
    if unit == "pp":
        return f"{number:+.1f} pp"
    if unit == "index":
        return f"{number:,.0f}"
    return f"{number:+,.1f}" if signed else f"{number:,.1f}"


def _kpi_delta_class(delta: Any, direction: Any) -> str:
    if delta is None or float(delta) == 0:
        return "neutral"
    is_positive = float(delta) > 0
    is_favourable = is_positive if direction != "inverse" else not is_positive
    return "positive" if is_favourable else "negative"


def render_chart_panel_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<p>{escape(subtitle)}</p>' if subtitle else ""
    html = (
        '<div class="dashboard-chart-panel__header">'
        f"<h3>{escape(title)}</h3>{subtitle_html}"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_page_summary(summary: Mapping[str, Any] | None, *, label: str | None = None) -> None:
    if not summary:
        return
    headline = summary.get("headline")
    body = summary.get("body")
    if not headline and not body:
        return
    eyebrow_html = f'<div class="dashboard-eyebrow">{escape(label)}</div>' if label else ""
    headline_html = f"<h3>{escape(str(headline))}</h3>" if headline else ""
    body_html = f"<p>{escape(str(body))}</p>" if body else ""
    html = (
        '<section class="dashboard-summary-panel">'
        f"{eyebrow_html}{headline_html}{body_html}"
        "</section>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_chart_insight(text: str | None, *, label: str = "Insight") -> None:
    if not text:
        return
    st.markdown(
        f'<aside class="dashboard-insight"><strong>{escape(label)}</strong><p>{escape(text)}</p></aside>',
        unsafe_allow_html=True,
    )


def render_data_freshness_note(text: str) -> None:
    st.markdown(f'<p class="dashboard-freshness-note">{escape(text)}</p>', unsafe_allow_html=True)


def render_methodology_note(text: str) -> None:
    html = (
        '<section class="dashboard-methodology-note">'
        f"<h3>Methodology</h3><p>{escape(text)}</p>"
        "</section>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(message: str = "No data is available for this view.") -> None:
    st.markdown(
        f'<section class="dashboard-empty-state"><p>{escape(message)}</p></section>',
        unsafe_allow_html=True,
    )
