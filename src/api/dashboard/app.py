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

page_nav = st.navigation(pages=[home_page, macropulse_page])
page_nav.run()


# python -m streamlit run .\src\api\dashboard\app.py