import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db_conn
from src.api.schemas.financial_markets import FinancialMarketsResponse
from src.api.services.financial_markets_api import FinancialMarketsDataError
from src.api.services.page_data import get_financial_markets_page


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=FinancialMarketsResponse)
def get_financial_markets_summary(db: sqlite3.Connection = Depends(get_db_conn)) -> FinancialMarketsResponse:
    try:
        return get_financial_markets_page(db)
    except FinancialMarketsDataError:
        logger.error("Financial Markets prepared data is unavailable")
        raise HTTPException(status_code=503, detail="Financial Markets data is currently unavailable.")
    except Exception:
        logger.exception("Financial Markets response assembly failed")
        raise HTTPException(status_code=503, detail="Financial Markets data could not be loaded.")
