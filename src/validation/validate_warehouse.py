"""Lightweight deployment validation for the generated SQLite warehouse."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from src.api.services.page_data import (
    get_financial_markets_page,
    get_global_flows_page,
    get_home_page,
    get_housing_credit_page,
    get_macro_pulse_page,
    get_monetary_policy_page,
)
from src.database.database_manager import configured_database_path, open_readonly_connection


REQUIRED_TABLES = {
    "economic_series",
    "kpi_cards",
    "chart_macropulse_egm",
    "chart_macropulse_ib",
    "chart_macropulse_lbh",
    "chart_monetary_policy_mp1",
    "chart_monetary_policy_mp2",
    "chart_monetary_policy_mp3",
    "chart_housing_credit_hc1",
    "chart_housing_credit_hc2",
    "chart_housing_credit_hc3",
    "chart_housing_credit_hc4",
    "chart_financial_markets_fm1",
    "chart_financial_markets_fm2_daily",
    "chart_financial_markets_fm2_monthly",
    "chart_financial_markets_fm3",
    "chart_global_flows_gf1",
    "chart_global_flows_gf2",
    "chart_global_flows_gf3",
}

REQUIRED_METRICS = {
    "GDP_QOQ",
    "CPI",
    "UNRATE",
    "BANK_RATE_DA",
    "UK_HPI_INDEX_UK",
    "FTSE_100_close",
}


class WarehouseValidationError(RuntimeError):
    """Raised when the generated warehouse is incomplete or corrupt."""


def _validate_page_services(connection: sqlite3.Connection) -> None:
    builders = (
        ("Home", get_home_page),
        ("Macro Pulse", get_macro_pulse_page),
        ("Monetary Policy", get_monetary_policy_page),
        ("Housing and Credit", get_housing_credit_page),
        ("Financial Markets", get_financial_markets_page),
        ("Global Flows", get_global_flows_page),
    )
    for name, builder in builders:
        try:
            builder(connection)
        except Exception as exc:
            raise WarehouseValidationError(
                f"{name} page service could not build its response: {exc}"
            ) from exc


def validate_warehouse(
    path: str | Path | None = None,
    *,
    validate_page_services: bool = True,
) -> dict[str, int | str]:
    """Validate integrity, required data and page-level service construction."""
    database_path = configured_database_path(path)
    if not database_path.is_file():
        raise WarehouseValidationError(f"Warehouse does not exist: {database_path}")
    if database_path.stat().st_size == 0:
        raise WarehouseValidationError(f"Warehouse is empty: {database_path}")

    try:
        connection = open_readonly_connection(database_path)
    except Exception as exc:
        raise WarehouseValidationError(f"Warehouse could not be opened: {exc}") from exc

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if not integrity or str(integrity[0]).lower() != "ok":
            raise WarehouseValidationError(
                f"SQLite integrity_check failed: {integrity[0] if integrity else 'no result'}"
            )

        present_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing_tables = sorted(REQUIRED_TABLES - present_tables)
        if missing_tables:
            raise WarehouseValidationError(
                "Required tables are missing: " + ", ".join(missing_tables)
            )

        empty_tables = [
            table
            for table in sorted(REQUIRED_TABLES)
            if connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0
        ]
        if empty_tables:
            raise WarehouseValidationError(
                "Required tables contain no rows: " + ", ".join(empty_tables)
            )

        metric_rows = connection.execute(
            "SELECT DISTINCT metric_id FROM economic_series"
        ).fetchall()
        present_metrics = {row[0] for row in metric_rows}
        missing_metrics = sorted(REQUIRED_METRICS - present_metrics)
        if missing_metrics:
            raise WarehouseValidationError(
                "Core public metrics are missing: " + ", ".join(missing_metrics)
            )

        if validate_page_services:
            _validate_page_services(connection)
    except sqlite3.Error as exc:
        raise WarehouseValidationError(f"SQLite validation query failed: {exc}") from exc
    finally:
        connection.close()

    return {
        "database": str(database_path),
        "tables": len(REQUIRED_TABLES),
        "core_metrics": len(REQUIRED_METRICS),
        "page_services": 6 if validate_page_services else 0,
    }


def main() -> None:
    try:
        summary = validate_warehouse()
    except WarehouseValidationError as exc:
        print(f"Warehouse validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(
        "Warehouse validation passed: "
        f"{summary['tables']} required tables, "
        f"{summary['core_metrics']} core metrics and "
        f"{summary['page_services']} page services."
    )


if __name__ == "__main__":
    main()
