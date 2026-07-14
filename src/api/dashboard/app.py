import requests
import streamlit as st

from src.utilities.config_loader import load_config
from src.utilities.build_url import build_chart_endpoint

# Helpers
endpoint = load_config('endpoints', 'base', 'fastapi')
chart_configs = load_config('charts')
pages = list(chart_configs.keys())

st.title('Macro UK Dashboard')
st.write('Welcome! use the sidebar to navigate between pages')






