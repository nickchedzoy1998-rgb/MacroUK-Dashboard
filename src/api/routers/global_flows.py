import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db_conn
from src.api.schemas.global_flows import GlobalFlowsResponse
from src.api.services.global_flows_api import GlobalFlowsDataError, build_global_flows_response


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=GlobalFlowsResponse)
def get_global_flows_summary(db: sqlite3.Connection = Depends(get_db_conn)) -> GlobalFlowsResponse:
    try: return build_global_flows_response(db)
    except GlobalFlowsDataError:
        logger.error("Global Flows prepared data is unavailable")
        raise HTTPException(status_code=503, detail="Global Flows data is currently unavailable.")
    except Exception:
        logger.exception("Global Flows response assembly failed")
        raise HTTPException(status_code=503, detail="Global Flows data could not be loaded.")
