"""Compare two countries side by side over a shared year range."""

import os
import numpy as np
import streamlit as st
from powering_planet import config as c
from powering_planet import dataset as d
from powering_planet import metrics as m
from powering_planet import plots as p

data_file = os.path.join(os.path.dirname(__file__), "..", d.DEFAULT_DATA_PATH)
df = st.cache_data(d.load_data)(data_file)

st.title("Country Comparator")

countries = d.get_countries(df)

idx_1 = countries.index("Italy") if "Italy" in countries else 0
idx_2 = countries.index("Germany") if "Germany" in countries else min(1, len(countries) - 1)

country_1 = st.sidebar.selectbox("First country", countries, index=idx_1)
country_2 = st.sidebar.selectbox("Second country", countries, index=idx_2)

# Raise warning is same country twice
if country_1 == country_2:
    st.warning("Choose two different countries to compare.")

full_1 = d.filter_country(df, country_1)
full_2 = d.filter_country(df, country_2)

min_y = int(max(full_1["year"].min(), full_2["year"].min()))
max_y = int(min(full_1["year"].max(), full_2["year"].max()))
default_start = max(min_y, max_y - 30)
years = st.sidebar.slider("Year range", min_y, max_y, (default_start, max_y))

cdf_1 = d.filter_country(df, country_1, years=years)
cdf_2 = d.filter_country(df, country_2, years=years)

left_col, right_col = st.columns(2)
for col_ui, cdf_self, name_self, cdf_other in [
    (left_col, cdf_1, country_1, cdf_2),
    (right_col, cdf_2, country_2, cdf_1),
]:
    with col_ui:
        st.subheader(name_self)
        dec = d.decoupling_status(cdf_self)
        st.caption(f"Decoupling: {dec['status']}")

        co2_1, _ = d.latest_value(cdf_self, "co2")
        eng_1, _ = d.latest_value(cdf_self, "total_energy_twh")
        gdp_1, _ = d.latest_value(cdf_self, "gdp_pc_ppp")
        low_1, _ = d.latest_value(cdf_self, "low_carbon_energy_share_pct")

        co2_2, _ = d.latest_value(cdf_other, "co2")
        eng_2, _ = d.latest_value(cdf_other, "total_energy_twh")
        gdp_2, _ = d.latest_value(cdf_other, "gdp_pc_ppp")
        low_2, _ = d.latest_value(cdf_other, "low_carbon_energy_share_pct")

        col_a, col_b = st.columns(2)
        col_a.metric(
            "CO2",
            "N/A" if np.isnan(co2_1) else f"{co2_1:,.1f} Mt",
            delta=m.fmt_diff(co2_1, co2_2, "+,.1f", " Mt"),
            delta_color="inverse",
        )
        col_b.metric(
            "Total Energy",
            "N/A" if np.isnan(eng_1) else f"{eng_1:,.1f} TWh",
            delta=m.fmt_diff(eng_1, eng_2, "+,.1f", " TWh"),
            delta_color="off",
        )
        col_a.metric(
            "GDP / Capita",
            "N/A" if np.isnan(gdp_1) else f"${gdp_1:,.0f}",
            delta=m.fmt_diff(gdp_1, gdp_2, "+,.0f"),
        )
        col_b.metric(
            "Low-Carbon Share",
            "N/A" if np.isnan(low_1) else f"{low_1:,.1f}%",
            delta=m.fmt_diff(low_1, low_2, "+,.1f", "%"),
        )

st.divider()
st.subheader("Trend Comparison")

indicator_map = c.FEATURE_OPTIONS
ind_label = st.selectbox("Select feature to compare", list(indicator_map.keys()))
ind_col = indicator_map[ind_label]

latest_1, yr_1 = d.latest_value(cdf_1, ind_col)
latest_2, yr_2 = d.latest_value(cdf_2, ind_col)
m_left, m_right = st.columns(2)
m_left.metric(
    f"{country_1} ({yr_1})" if yr_1 else country_1,
    "N/A" if np.isnan(latest_1) else f"{latest_1:,.2f}",
)
m_right.metric(
    f"{country_2} ({yr_2})" if yr_2 else country_2,
    "N/A" if np.isnan(latest_2) else f"{latest_2:,.2f}",
)

fig_line = p.make_comparison_line(cdf_1, country_1, cdf_2, country_2, ind_col, ind_label)
if fig_line is None:
    st.info("No data available for this feature.")
else:
    st.plotly_chart(fig_line, width="stretch")

st.divider()
st.subheader("Energy Mix Comparison")

mix_options = {
    "Fossil vs. Low-Carbon": c.OVERVIEW_SOURCES,
    "Fossil Fuels by Source": c.FOSSIL_SOURCES,
    "Low-Carbon Energy by Source": c.LOW_CARBON_SOURCES,
}
mix_choice = st.selectbox("Select energy mix chart", list(mix_options.keys()))
selected_sources = mix_options[mix_choice]

mix_left, mix_right = st.columns(2)
with mix_left:
    st.plotly_chart(
        p.make_energy_chart(cdf_1, selected_sources, f"{country_1}: {mix_choice}"),
        width="stretch",
    )
with mix_right:
    st.plotly_chart(
        p.make_energy_chart(cdf_2, selected_sources, f"{country_2}: {mix_choice}"),
        width="stretch",
    )