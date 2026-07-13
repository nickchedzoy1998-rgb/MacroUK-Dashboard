import requests
import pandas as pd
from pathlib import Path
import plotly.express as px
import streamlit as st
import numpy as np

from src.utilities.config_loader import load_config
from src.utilities.http_client import fetch_json

charts_config = load_config('charts', 'MacroPulse')
metric_ids = charts_config['EGM']['metrics']


class Dashboard:
    def __init__(self):
        self.url = load_config('endpoints', 'base', 'fastapi')
        st.title('Macro UK Dashboard')

    
    def pull_from_api(self, metric_id=None):        
        if metric_id is not None:
            url = self.url + f'/{metric_id}'
        else:
            url = self.url

        fast_api_json = fetch_json(url)
        df = pd.DataFrame(fast_api_json)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            return df
        
        return pd.DataFrame()

    def egm_chart(self, df):
        metric_name = df['metric_name'].unique()[0]
        value_type = df['unit'].unique()[0]

        fig = px.line(
            df, x='date', y='value', 
            labels={'value': value_type, 'date': 'Date'},
            title = metric_name
        )

        # Customize layout to make it fit beautifully in Streamlit
        fig.update_layout(template="plotly_dark", hovermode="x unified")

        # 4. Display the Plotly chart in Streamlit
        st.plotly_chart(fig, width='stretch')

if __name__ == '__main__':
    dashboard = Dashboard()

    for id in metric_ids:
        print(dashboard.pull_from_api(id))

# python -m src.dashboard.macro_pulse
