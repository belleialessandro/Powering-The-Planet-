"""Compare two countries side by side over a shared year range."""

import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

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
from powering_planet.plots import make_energy_chart


@st.cache_data
def cached_load_data(path):
    """Load the dataset once and cache it across interactions."""
    return load_data(path)


def show_country_summary(cdf, name):
    """Show key metrics for one country."""
    st.subheader(name)
    dec = decoupling_status(cdf)
    st.caption(f"Decoupling: {dec['status']}")

    co2_val, _ = latest_value(cdf, "co2")
    eng_val, _ = latest_value(cdf, "total_energy_twh")
    gdp_pc_val, _ = latest_value(cdf, "gdp_pc_ppp")
    low_c_val, _ = latest_value(cdf, "low_carbon_energy_share_pct")

    col_a, col_b = st.columns(2)
    col_a.metric("CO2", "N/A" if np.isnan(co2_val) else f"{co2_val:,.1f} Mt")
    col_b.metric("Total Energy", "N/A" if np.isnan(eng_val) else f"{eng_val:,.1f} TWh")
    col_a.metric("GDP / Capita", "N/A" if np.isnan(gdp_pc_val) else f"${gdp_pc_val:,.0f}")
    col_b.metric("Low-Carbon Share", "N/A" if np.isnan(low_c_val) else f"{low_c_val:,.1f}%")


def get_feature_options(df):
    """Return a dictionary of friendly feature labels to column names present in df."""
    all_features = {
        "Low-Carbon Energy Share (%)": "low_carbon_energy_share_pct",
        "Renewables Share (%)": "renewables_energy_share_pct",
        "Fossil Fuels Share (%)": "fossil_fuels_energy_share_pct",
        "Coal Share (%)": "coal_energy_share_pct",
        "Oil Share (%)": "oil_energy_share_pct",
        "Gas Share (%)": "gas_energy_share_pct",
        "Nuclear Share (%)": "nuclear_energy_share_pct",
        "Hydro Share (%)": "hydro_energy_share_pct",
        "Wind Share (%)": "wind_energy_share_pct",
        "Solar Share (%)": "solar_energy_share_pct",
        "Biofuels Share (%)": "biofuels_energy_share_pct",
        "Other Renewables Share (%)": "other_renewables_including_bioenergy_energy_share_pct",
        "Total Energy (TWh)": "total_energy_twh",
        "Total CO2 (Mt)": "co2",
        "CO2 per Capita (t)": "co2_per_capita",
        "Share of Global CO2 (%)": "share_global_co2",
        "Carbon Intensity (Mt/TWh)": "carbon_intensity_energy",
        "Energy Intensity (TWh/$B GDP)": "energy_intensity_gdp",
        "GDP per Capita PPP ($)": "gdp_pc_ppp",
        "GDP PPP ($)": "gdp_ppp",
        "Population": "population",
    }
    available = {}
    for label, col in all_features.items():
        if col in df.columns:
            available[label] = col
    return available


data_file = os.path.join(os.path.dirname(__file__), "..", DEFAULT_DATA_PATH)
df = cached_load_data(data_file)

st.title("Country Comparator")

countries = get_countries(df)

idx_1 = countries.index("Italy") if "Italy" in countries else 0
idx_2 = countries.index("Germany") if "Germany" in countries else min(1, len(countries) - 1)

country_1 = st.sidebar.selectbox("First country", countries, index=idx_1)
country_2 = st.sidebar.selectbox("Second country", countries, index=idx_2)

if country_1 == country_2:
    st.warning("Choose two different countries to compare.")

full_1 = filter_country(df, country_1)
full_2 = filter_country(df, country_2)

min_y = int(max(full_1["year"].min(), full_2["year"].min()))
max_y = int(min(full_1["year"].max(), full_2["year"].max()))
default_start = max(min_y, max_y - 30)
years = st.sidebar.slider("Year range", min_y, max_y, (default_start, max_y))

cdf_1 = filter_country(df, country_1, years=years)
cdf_2 = filter_country(df, country_2, years=years)

left_col, right_col = st.columns(2)
with left_col:
    show_country_summary(cdf_1, country_1)
with right_col:
    show_country_summary(cdf_2, country_2)

st.divider()
st.subheader("Trend Comparison")

indicator_map = get_feature_options(df)
ind_label = st.selectbox("Select feature to compare", list(indicator_map.keys()))
ind_col = indicator_map[ind_label]

latest_1, yr_1 = latest_value(cdf_1, ind_col)
latest_2, yr_2 = latest_value(cdf_2, ind_col)
m_left, m_right = st.columns(2)
m_left.metric(
    f"{country_1} ({yr_1})" if yr_1 else country_1,
    "N/A" if np.isnan(latest_1) else f"{latest_1:,.2f}",
)
m_right.metric(
    f"{country_2} ({yr_2})" if yr_2 else country_2,
    "N/A" if np.isnan(latest_2) else f"{latest_2:,.2f}",
)

sub_1 = cdf_1[["year", ind_col]].dropna().assign(Country=country_1)
sub_2 = cdf_2[["year", ind_col]].dropna().assign(Country=country_2)
combined = pd.concat([sub_1, sub_2], ignore_index=True)

if combined.empty:
    st.info("No data available for this feature.")
else:
    fig_line = px.line(
        combined,
        x="year",
        y=ind_col,
        color="Country",
        title=f"{ind_label}: {country_1} vs. {country_2}",
        labels={"year": "Year", ind_col: ind_label},
        template="plotly_white",
    )
    st.plotly_chart(fig_line, width="stretch")

st.divider()
st.subheader("Energy Mix Comparison")

mix_options = {
    "Fossil vs. Low-Carbon": OVERVIEW_SOURCES,
    "Fossil Fuels by Source": FOSSIL_SOURCES,
    "Low-Carbon Energy by Source": LOW_CARBON_SOURCES,
}
mix_choice = st.selectbox("Select energy mix chart", list(mix_options.keys()))
selected_sources = mix_options[mix_choice]

mix_left, mix_right = st.columns(2)
with mix_left:
    st.plotly_chart(
        make_energy_chart(cdf_1, selected_sources, f"{country_1}: {mix_choice}"),
        width="stretch",
    )
with mix_right:
    st.plotly_chart(
        make_energy_chart(cdf_2, selected_sources, f"{country_2}: {mix_choice}"),
        width="stretch",
    )