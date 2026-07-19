import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db_conn
from src.api.schemas.housing_credit import HousingCreditResponse
from src.api.services.housing_credit_api import HousingCreditDataError, build_housing_credit_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=HousingCreditResponse)
def get_housing_credit_summary(db: sqlite3.Connection = Depends(get_db_conn)) -> HousingCreditResponse:
    try:
        return build_housing_credit_response(db)
    except HousingCreditDataError:
        logger.error("Housing and Consumer Credit prepared data is unavailable")
        raise HTTPException(status_code=503, detail="Housing and Consumer Credit data is currently unavailable.")
    except Exception:
        logger.exception("Housing and Consumer Credit response assembly failed")
        raise HTTPException(status_code=503, detail="Housing and Consumer Credit data could not be loaded.")
