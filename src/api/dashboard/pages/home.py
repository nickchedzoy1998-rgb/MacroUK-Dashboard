import streamlit as st


st.title("UK Economic Dashboard")

st.write(
    "Track the health of the UK economy through growth, inflation, "
    "employment, monetary policy, housing, and financial markets."
)

st.subheader("Dashboard overview")

st.write("Headline KPIs:")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric(label="GDP Growth", value="-")

with col2:
    with st.container(border=True):
        st.metric(label="Inflation", value="-")

with col3:
    with st.container(border=True):
        st.metric(label="Unemployment Rate", value="-")

col4, col5, col6 = st.columns(3)

with col4:
    with st.container(border=True):
        st.metric(label="Bank Rate", value="-")

with col5:
    with st.container(border=True):    
        st.metric(label="UK house price growth", value="-")

with col6:
    with st.container(border=True):
        st.metric(label="FTSE 250", value="-")

if st.button("Go to MacroPulse Deep Dive"):
    st.switch_page('pages/macro_pulse.py')

st.caption('Date Freshness Note Placeholder')