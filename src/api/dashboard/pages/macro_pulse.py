import streamlit as st
import requests
import logging

from src.utilities.build_url import build_chart_endpoint
from src.utilities.config_loader import load_config

# Helpers:
macro_pulse_config = load_config('charts', 'MacroPulse')
chart_ids = list(macro_pulse_config.keys())

st.title('Macro-Pulse')
st.write('This section looks at the foundational health of the economy—growth, inflation, and employment.')

def get_chart_data(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        logging.info('Successfully contacted API')
        st.write(data)
    
    else:
        st.error(f'Failed to fetch data from API from {api_url}')


def main():
    logging.info('Attempting to pull data from API')

    for id in chart_ids:
        logging.info(f'Extracting data for chart: {id}')
        api_endpoint = build_chart_endpoint('MacroPulse', id)
        get_chart_data(api_endpoint)

if __name__ == '__main__':
    main()