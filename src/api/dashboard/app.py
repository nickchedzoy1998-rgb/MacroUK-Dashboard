import streamlit as st

# Page Config:
st.set_page_config(
    page_title='Macro UK Dashboard',
    page_icon='💷',
    layout='wide'
)

# Pages:
home_page = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
macropulse_page = st.Page("pages/macro_pulse.py", title="Macro Pulse", icon="📈")
monetary_policy_page = st.Page("pages/monetary_policy.py", title="Monetary Policy & Liquidity", icon="🏦")
housing_credit_page = st.Page("pages/housing_credit.py", title="Housing Market & Consumer Credit", icon="🏠")
financial_markets_page = st.Page("pages/financial_markets.py", title="Financial Markets & Equities", icon="📊")
global_flows_page = st.Page("pages/global_flows.py", title="Currency, Commodities & Fixed Income", icon="🌐")

page_nav = st.navigation(pages=[home_page, macropulse_page, monetary_policy_page, housing_credit_page, financial_markets_page, global_flows_page])
page_nav.run()


# python -m streamlit run .\src\api\dashboard\app.py
