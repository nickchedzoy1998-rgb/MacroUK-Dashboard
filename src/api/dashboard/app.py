import requests

from src.utilities.config_loader import load_config
from src.utilities.http_client import fetch_json
from src.utilities.build_url import build_chart_endpoint

# Helpers
endpoint = load_config('endpoints', 'base', 'fastapi')
data = fetch_json()
chart_configs = load_config('charts')
pages = list(chart_configs.keys())




