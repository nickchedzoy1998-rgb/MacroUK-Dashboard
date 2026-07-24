import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db_conn
from src.api.schemas.home import HomeSummaryResponse
from src.api.services.page_data import get_home_page


router = APIRouter()


@router.get("/summary", response_model=HomeSummaryResponse)
def get_home_summary(db: sqlite3.Connection = Depends(get_db_conn)) -> HomeSummaryResponse:
    try:
        return get_home_page(db)
    except (sqlite3.Error, RuntimeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read Home KPI data from kpi_cards: {exc}",
        ) from exc
