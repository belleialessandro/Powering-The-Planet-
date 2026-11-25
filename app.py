"""Powering the Planet: Streamlit multi-page entry point."""

import streamlit as st

# Configure browser tab title, icon, and wide layout before rendering pages
st.set_page_config(page_title="Powering the Planet", page_icon="🌍", layout="wide")

# Register all app pages explicitly and set Country Profile as the default landing page
pg = st.navigation(
    [
        st.Page("pages/country_profile.py", title="Country Profile", icon="🌍", default=True),
        st.Page("pages/ranking.py", title="Country Ranking", icon="🏆"),
        st.Page("pages/compare.py", title="Country Comparator", icon="⚖️"),
    ]
)
pg.run()
