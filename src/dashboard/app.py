import requests
import pandas as pd
from pathlib import Path
import plotly.express as px
import streamlit as st
import numpy as np

from src.utilities.config_loader import load_config
from src.utilities.http_client import extract


class Dashboard:
    def __init__(self):
        self.cpi_url = load_config('endpoints', 'fastapi', 'cpi')

    def pull(self):
        fast_api_json = extract(self.cpi_url)
        df = pd.DataFrame(fast_api_json)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            return df
        
        return pd.DataFrame()

    def dashboard_app(self):
        st.title('Macro UK Dashboard')

        df = self.pull()

        # Harcoding Graph name in first draft
        fig = px.line(
            df, x='date', y='value', 
            labels={'value': 'CPI', 'date': 'Date'},
            title = 'Consumer Price Index History'
        )

        # Customize layout to make it fit beautifully in Streamlit
        fig.update_layout(template="plotly_dark", hovermode="x unified")

        # 4. Display the Plotly chart in Streamlit
        st.plotly_chart(fig, width='stretch')


if __name__ == '__main__':
    dash = Dashboard()
    dash.dashboard_app()

    # python -m streamlit run src/dashboard/app.py