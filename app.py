"""Streamlit entry point for Powering the Planet."""

import streamlit as st

st.set_page_config(page_title="Powering the Planet", page_icon="🌍", layout="wide")

pages = [
    st.Page("pages/country_profile.py", title="Country Profile", default=True),
    st.Page("pages/ranking.py", title="Ranking"),
    st.Page("pages/compare.py", title="Comparator"),
]

st.navigation(pages).run()
