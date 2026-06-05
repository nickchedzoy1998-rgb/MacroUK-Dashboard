import requests
import pandas as pd
from pathlib import Path
from src.etl.fetch_ons import extract
import plotly.express as px

from src.utilities.config_loader import load_config

px.data.tips

# Helpers
cpi_url = load_config('endpoints', 'fastapi', 'cpi')


if __name__ == '__main__':
    raw = extract(cpi_url)
    df = pd.DataFrame(raw)
    
    px.line(df,)

