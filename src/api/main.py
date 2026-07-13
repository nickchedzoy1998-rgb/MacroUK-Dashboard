from fastapi import FastAPI
import sqlite3
from pathlib import Path

from src.utilities.config_loader import load_config
from src.api.routers.macro_pulse import router as macro_pulse_router

app = FastAPI(title='MACRO UK DASHBOARD API')

# Simple endpoint that shows web server is physically running when we visit the base URL
@app.get("/")
def read_root():
    return {"message": "Welcome to the Macro UK Dashboard API. Head to /docs for the interactive UI."}