import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db_conn
from src.api.schemas.monetary_policy import MonetaryPolicyResponse
from src.api.services.monetary_policy_api import MonetaryPolicyDataError
from src.api.services.page_data import get_monetary_policy_page


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=MonetaryPolicyResponse)
def get_monetary_policy_summary(db: sqlite3.Connection = Depends(get_db_conn)) -> MonetaryPolicyResponse:
    try:
        return get_monetary_policy_page(db)
    except MonetaryPolicyDataError:
        logger.error("Monetary Policy prepared data is unavailable")
        raise HTTPException(status_code=503, detail="Monetary Policy data is currently unavailable.")
    except Exception:
        logger.exception("Monetary Policy response assembly failed")
        raise HTTPException(status_code=503, detail="Monetary Policy data could not be loaded.")
