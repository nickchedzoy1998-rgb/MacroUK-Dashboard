import sqlite3
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db_conn
from src.api.schemas.home import HomeKPI, HomeSummaryResponse
from src.utilities.config_loader import load_config

home_config = load_config('charts', 'Home')
router = APIRouter()


def normalize_date(value):
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
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                return value
    return value


@router.get('/summary', response_model=HomeSummaryResponse)
def get_home_summary(db: sqlite3.Connection = Depends(get_db_conn)):
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT
                kpi_id,
                metric_id,
                value,
                delta,
                date
            FROM kpi_cards
            """
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError as exc:
        raise HTTPException(
            status_code=500,
            detail=f'Unable to read Home KPI data from kpi_cards: {exc}'
        ) from exc

    row_map = {}
    for row in rows:
        row_map[row['kpi_id']] = {
            'kpi_id': row['kpi_id'],
            'metric_id': row['metric_id'],
            'value': float(row['value']),
            'delta': None if row['delta'] is None else float(row['delta']),
            'date': normalize_date(row['date']),
        }

    kpis = []
    for kpi_id, config in home_config.items():
        if kpi_id not in row_map:
            raise HTTPException(
                status_code=500,
                detail=f"Configured KPI '{kpi_id}' missing from kpi_cards"
            )

        row = row_map[kpi_id]
        kpis.append(
            HomeKPI(
                **row,
                name=config['name'],
                comparison_type=config['comparison_type'],
                comparison_label=config.get('comparison_label'),
                delta_unit=config.get('delta_unit'),
                delta_direction=config.get('delta_direction'),
            )
        )

    return HomeSummaryResponse(kpis=kpis)
