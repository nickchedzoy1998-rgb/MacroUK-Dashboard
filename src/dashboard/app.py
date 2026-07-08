import requests
import pandas as pd
from pathlib import Path
import plotly.express as px
import streamlit as st
import numpy as np

from src.utilities.config_loader import load_config
from src.utilities.http_client import fetch_json


class Dashboard:
    def __init__(self):
        self.url = load_config('endpoints', 'base', 'fastapi')
        st.title('Macro UK Dashboard')

        metric_options = []
        metric_keys = ['ons_metrics', 'boe_metrics', 'y_finance_metrics', 'hmlr_metrics', 'hmt_metrics']

        for key in metric_keys:
            options = list(load_config('metric_manifest', key).keys())
            metric_options.extend(options)
        
        self.metric_options = metric_options
  
    def pull(self, metric_id=None):
        metric_id = st.selectbox("Select a metric to view:", options=self.metric_options)

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

    def chart(self, df):
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

    df = dashboard.pull()

    # st.dataframe(df)
    dashboard.chart(df)

    # python -m streamlit run src/dashboard/app.py