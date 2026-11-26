"""Country profile page: energy mix, decoupling, phase-out simulator, and table."""

import os
import numpy as np
import pandas as pd
import streamlit as st

from powering_planet.analysis import simulate_phase_out
from powering_planet.dataset import (
    DEFAULT_DATA_PATH,
    decoupling_status,
    filter_country,
    get_countries,
    latest_value,
    load_data,
)
from powering_planet.metrics import (
    FOSSIL_SOURCES,
    LOW_CARBON_SOURCES,
    OVERVIEW_SOURCES,
)
from powering_planet.plots import make_decoupling_chart, make_energy_chart, make_energy_pie


@st.cache_data
def cached_load_data(path):
    """Load the dataset once and cache it across interactions."""
    return load_data(path)


data_file = os.path.join(os.path.dirname(__file__), "..", DEFAULT_DATA_PATH)
df = cached_load_data(data_file)

countries = get_countries(df)

default_index = countries.index("Italy") if "Italy" in countries else 0
country = st.sidebar.selectbox("Country", countries, index=default_index)

full_country_df = filter_country(df, country)
min_year = int(full_country_df["year"].min())
max_year = int(full_country_df["year"].max())
default_start = max(min_year, max_year - 30)
years = st.sidebar.slider("Year range", min_year, max_year, (default_start, max_year))

cdf = filter_country(df, country, years=years)
st.title(f"{country} ({years[0]}–{years[1]})")

co2_val, co2_yr = latest_value(cdf, "co2")
gdp_val, gdp_yr = latest_value(cdf, "gdp_ppp")
eng_val, eng_yr = latest_value(cdf, "total_energy_twh")
dec = decoupling_status(cdf)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    f"CO2 ({co2_yr})" if co2_yr else "CO2",
    "N/A" if np.isnan(co2_val) else f"{co2_val:,.1f} Mt",
)
c2.metric(
    f"GDP PPP ({gdp_yr})" if gdp_yr else "GDP PPP",
    "N/A" if np.isnan(gdp_val) else f"${gdp_val / 1e9:,.1f} B",
)
c3.metric(
    f"Total Energy ({eng_yr})" if eng_yr else "Total Energy",
    "N/A" if np.isnan(eng_val) else f"{eng_val:,.1f} TWh",
)
c4.metric(
    "Decoupling",
    dec["status"],
    delta=None if np.isnan(dec["co2_cagr"]) else f"{dec['co2_cagr']:+.1f}%/yr CO2",
    delta_color="inverse",
)

pie_specs = [
    (OVERVIEW_SOURCES, "Overview"),
    (FOSSIL_SOURCES, "Fossil Fuels"),
    (LOW_CARBON_SOURCES, "Low-Carbon"),
]
pie_cols = st.columns(3)
for idx in range(len(pie_specs)):
    sources, label = pie_specs[idx]
    with pie_cols[idx]:
        pie_fig = make_energy_pie(cdf, sources, label, height=260)
        if pie_fig is None:
            st.caption(f"{label}: no data")
        else:
            st.plotly_chart(pie_fig, width="stretch")

st.divider()
st.subheader("Energy Mix Over Time")

st.plotly_chart(
    make_energy_chart(cdf, OVERVIEW_SOURCES, "Fossil vs. Low-Carbon Energy"),
    width="stretch",
)
st.plotly_chart(
    make_energy_chart(cdf, FOSSIL_SOURCES, "Fossil Fuels by Source"),
    width="stretch",
)
st.plotly_chart(
    make_energy_chart(cdf, LOW_CARBON_SOURCES, "Low-Carbon Energy by Source"),
    width="stretch",
)

st.divider()
st.subheader("GDP, Energy, and CO2 Trends")

dec_fig = make_decoupling_chart(cdf)
if dec_fig is None:
    st.info("Not enough overlapping years for the indexed chart.")
else:
    st.plotly_chart(dec_fig, width="stretch")

st.divider()
st.subheader("What-If Fossil Phase-Out Simulator")

valid_rows = cdf.dropna(subset=["total_energy_twh", "co2"])
if valid_rows.empty:
    st.info("No complete energy and CO2 rows in this year range.")
else:
    base_row = valid_rows.iloc[-1]
    st.caption(f"Baseline year: {int(base_row['year'])}")

    s1, s2, s3 = st.columns(3)
    coal_cut = s1.slider("Coal cut (%)", 0, 100, 50)
    oil_cut = s2.slider("Oil cut (%)", 0, 100, 25)
    gas_cut = s3.slider("Gas cut (%)", 0, 100, 25)

    sim = simulate_phase_out(base_row, coal_cut, oil_cut, gas_cut)
    m1, m2, m3 = st.columns(3)
    m1.metric("Baseline CO2", f"{sim['baseline_co2_mt']:,.1f} Mt")
    m2.metric(
        "Projected CO2",
        f"{sim['new_co2_mt']:,.1f} Mt",
        delta=f"-{sim['saved_co2_mt']:,.1f} Mt",
        delta_color="inverse",
    )
    m3.metric("Reduction", f"{sim['reduction_pct']:.1f}%")

st.divider()
st.subheader("Country Data Table")

table_cols = [
    "year",
    "population",
    "total_energy_twh",
    "coal_energy_share_pct",
    "oil_energy_share_pct",
    "gas_energy_share_pct",
    "nuclear_energy_share_pct",
    "hydro_energy_share_pct",
    "wind_energy_share_pct",
    "solar_energy_share_pct",
    "co2",
    "co2_per_capita",
    "gdp_pc_ppp",
    "gdp_ppp",
]
existing_cols = [col for col in table_cols if col in cdf.columns]
show_df = cdf[existing_cols].sort_values("year", ascending=False).reset_index(drop=True)
st.dataframe(show_df, width="stretch", hide_index=True)