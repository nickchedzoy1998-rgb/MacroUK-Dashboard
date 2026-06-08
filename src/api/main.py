import sqlite3
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd

from src.utilities.config_loader import load_config

database_name = load_config('settings', 'databases', 'economics_db')
DB_PATH = Path("data") / f"{database_name}.db"

app = FastAPI()

@app.get("/ready", tags=["Health"])
async def health_check():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        conn.close()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "database": "connected"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": f"disconnected: {str(e)}"}
        )
    
@app.get("/series")
async def get_series():
    try:
        conn = sqlite3.connect(DB_PATH)
        data = pd.read_sql_query("SELECT * FROM economic_series ORDER BY metric_id, date;", conn)

        if data.empty:
            return []
                                 
        data_json_dict = data.to_dict(orient='records')
        
        return data_json_dict
        
    except Exception as e:
        raise ConnectionError('Error getting data: {e}')
    

# Temp Function for Debugging
@app.get("/series/{metric_id}")
async def get_series(metric_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        data = pd.read_sql_query(
            "SELECT * FROM economic_series WHERE metric_id = ?;", 
            conn, 
            params=(metric_id.upper(),)
        )

        if data.empty:
            return []
                                 
        data_json_dict = data.to_dict(orient='records')
        
        return data_json_dict
        
    except Exception as e:
        raise ConnectionError('Error getting data: {e}')
    
# uvicorn src.api.main:app --reload