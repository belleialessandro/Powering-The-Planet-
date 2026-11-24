"""Powering the Planet: Streamlit multi-page entry point."""

import streamlit as st

st.set_page_config(page_title="Powering the Planet", page_icon="🌍", layout="wide")

pg = st.navigation(
    [
        st.Page("pages/country_profile.py", title="Country Profile", icon="🌍", default=True),
        st.Page("pages/ranking.py", title="Global Ranking", icon="🏆"),
        st.Page("pages/insights.py", title="Insights & Simulator", icon="📊"),
        st.Page("pages/compare.py", title="Compare 2 Countries", icon="⚖️"),
    ]
)
pg.run()
