# TEMP NOTES
# Make tables/ data available for dashboard but can't read local or sql
# SQL ---> HTML
# Create web link i.e. /egm that software (dashboard) navigates to

import sqlite3
from fastapi import FastAPI, APIRouter, Depends
from pathlib import Path
from typing import List

from src.utilities.config_loader import load_config
from src.api.schemas.macro_pulse import CHART_SCHEMAS
from src.api.dependencies import get_db_conn

# Helpers & Configs:
macropulse_config = load_config('charts', 'MacroPulse')
router = APIRouter()

def table(chart_id):
    suffix = str(chart_id).lower()
    return 'chart_macropulse_' + suffix


@router.get("/egm", response_model=List[CHART_SCHEMAS['EGM']])
def get_egm_data(db: sqlite3.Connection=Depends(get_db_conn)):
    table_name = table(chart_id='EGM')

    cursor = db.cursor()
    cursor.execute(f'SELECT * FROM {table_name} ORDER BY date ASC')

    return cursor.fetchall()


@router.get("/ib", response_model=List[CHART_SCHEMAS['IB']])
def get_ib_data(db: sqlite3.Connection=Depends(get_db_conn)):
    table_name = table(chart_id='IB')

    cursor = db.cursor()
    cursor.execute(f'SELECT * FROM {table_name} ORDER BY date ASC')

    return cursor.fetchall()
    

@router.get("/lbh", response_model=List[CHART_SCHEMAS['LBH']])
def get_lbh_data(db: sqlite3.Connection=Depends(get_db_conn)):
    table_name = table(chart_id='LBH')

    cursor = db.cursor()
    cursor.execute(f'SELECT * FROM {table_name} ORDER BY date ASC')

    return cursor.fetchall()