"""Framework-independent page data access shared by Streamlit and FastAPI."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

from src.api.schemas.home import HomeKPI, HomeSummaryResponse
from src.api.schemas.macro_pulse import MacroPulseResponse
from src.api.schemas.monetary_policy import MonetaryPolicyResponse
from src.api.schemas.housing_credit import HousingCreditResponse
from src.api.schemas.financial_markets import FinancialMarketsResponse
from src.api.schemas.global_flows import GlobalFlowsResponse
from src.api.services.financial_markets_api import build_financial_markets_response
from src.api.services.global_flows_api import build_global_flows_response
from src.api.services.home_summary import build_home_interpretation
from src.api.services.housing_credit_api import build_housing_credit_response
from src.api.services.macro_pulse_api import build_macro_pulse_response
from src.api.services.monetary_policy_api import build_monetary_policy_response
from src.database.database_manager import (
    configured_database_path,
    open_readonly_connection,
)
from src.utilities.config_loader import load_config


def _normalise_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return datetime.fromisoformat(value).date()
    return value


def build_home_response(connection: sqlite3.Connection) -> HomeSummaryResponse:
    """Build the Home response from SQLite without FastAPI dependencies."""
    config = load_config("charts", "Home")
    rows = connection.execute(
        "SELECT kpi_id, metric_id, value, delta, date FROM kpi_cards"
    ).fetchall()
    row_map = {
        row["kpi_id"]: {
            "kpi_id": row["kpi_id"],
            "metric_id": row["metric_id"],
            "value": float(row["value"]),
            "delta": None if row["delta"] is None else float(row["delta"]),
            "date": _normalise_date(row["date"]),
        }
        for row in rows
    }

    missing = [kpi_id for kpi_id in config if kpi_id not in row_map]
    if missing:
        raise RuntimeError(f"Configured Home KPIs missing from kpi_cards: {', '.join(missing)}")

    kpis = [
        HomeKPI(
            **row_map[kpi_id],
            name=item["name"],
            comparison_type=item["comparison_type"],
            comparison_label=item.get("comparison_label"),
            main_unit=item.get("main_unit"),
            delta_unit=item.get("delta_unit"),
            delta_direction=item.get("delta_direction"),
            description=item.get("description"),
        )
        for kpi_id, item in config.items()
    ]
    summary, highlights = build_home_interpretation(kpis, config)
    return HomeSummaryResponse(
        kpis=kpis,
        summary=asdict(summary),
        highlights=[asdict(highlight) for highlight in highlights],
    )


@contextmanager
def _connection(
    connection: sqlite3.Connection | None = None,
    database_path: str | Path | None = None,
) -> Iterator[sqlite3.Connection]:
    if connection is not None:
        yield connection
        return
    opened = open_readonly_connection(configured_database_path(database_path))
    try:
        yield opened
    finally:
        opened.close()


def get_home_page(
    connection: sqlite3.Connection | None = None,
    *,
    database_path: str | Path | None = None,
) -> HomeSummaryResponse:
    with _connection(connection, database_path) as db:
        return build_home_response(db)


def get_macro_pulse_page(
    connection: sqlite3.Connection | None = None,
    *,
    database_path: str | Path | None = None,
) -> MacroPulseResponse:
    with _connection(connection, database_path) as db:
        return build_macro_pulse_response(db)


def get_monetary_policy_page(
    connection: sqlite3.Connection | None = None,
    *,
    database_path: str | Path | None = None,
) -> MonetaryPolicyResponse:
    with _connection(connection, database_path) as db:
        return build_monetary_policy_response(db)


def get_housing_credit_page(
    connection: sqlite3.Connection | None = None,
    *,
    database_path: str | Path | None = None,
) -> HousingCreditResponse:
    with _connection(connection, database_path) as db:
        return build_housing_credit_response(db)


def get_financial_markets_page(
    connection: sqlite3.Connection | None = None,
    *,
    database_path: str | Path | None = None,
) -> FinancialMarketsResponse:
    with _connection(connection, database_path) as db:
        return build_financial_markets_response(db)


def get_global_flows_page(
    connection: sqlite3.Connection | None = None,
    *,
    database_path: str | Path | None = None,
) -> GlobalFlowsResponse:
    with _connection(connection, database_path) as db:
        return build_global_flows_response(db)
