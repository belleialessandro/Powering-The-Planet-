"""Country ranking page: leaderboard, podium, CSV download, and Top 10 chart."""

import os
import numpy as np
import pandas as pd
import streamlit as st

from powering_planet.dataset import (
    DEFAULT_DATA_PATH,
    filter_country,
    load_data,
    rank_countries,
)
from powering_planet.plots import make_top10_bar


@st.cache_data
def cached_load_data(path):
    """Load the dataset once and cache it across interactions."""
    return load_data(path)


data_file = os.path.join(os.path.dirname(__file__), "..", DEFAULT_DATA_PATH)
df = cached_load_data(data_file)

st.title("Country Ranking")

all_years = sorted(df["year"].dropna().astype(int).unique().tolist())
default_year = 2024 if 2024 in all_years else all_years[-1]
year = st.sidebar.selectbox("Year", all_years, index=all_years.index(default_year))

st.divider()
st.subheader("Transition Ranking")

metric_options = {
    "Low-Carbon Energy Share (%)": ("low_carbon_energy_share_pct", False),
    "Renewables Energy Share (%)": ("renewables_energy_share_pct", False),
    "Lowest Carbon Intensity (Mt/TWh)": ("carbon_intensity_energy", True),
    "Lowest Energy Intensity (TWh/$B GDP)": ("energy_intensity_gdp", True),
}
metric_label = st.selectbox("Rank by", list(metric_options.keys()))
sort_col, ascending = metric_options[metric_label]

ranked = rank_countries(df, year=year, sort_by=sort_col, ascending=ascending)

if ranked.empty:
    st.info("No data available for this year and metric.")
else:
    top3 = ranked.head(3)
    podium_cols = st.columns(len(top3))
    medals = ["1st", "2nd", "3rd"]
    for idx in range(len(top3)):
        row = top3.iloc[idx]
        val = row[sort_col]
        val_text = "N/A" if pd.isna(val) or np.isnan(val) else f"{val:,.2f}"
        podium_cols[idx].metric(f"{medals[idx]}: {row['country']}", val_text)

    table_cols = [
        "rank",
        "country",
        "iso_code",
        "low_carbon_energy_share_pct",
        "renewables_energy_share_pct",
        "carbon_intensity_energy",
        "co2_per_capita",
        "gdp_pc_ppp",
    ]
    existing_table_cols = [col for col in table_cols if col in ranked.columns]
    table_df = ranked[existing_table_cols]

    st.dataframe(table_df, width="stretch", hide_index=True)
    st.download_button(
        "Download ranking as CSV",
        data=table_df.to_csv(index=False),
        file_name=f"ranking_{year}.csv",
        mime="text/csv",
    )

st.divider()
st.subheader("Top 10 Countries by Indicator")

feature_options = {
    "Total Energy (TWh)": "total_energy_twh",
    "Total CO2 (Mt)": "co2",
    "CO2 per Capita (t)": "co2_per_capita",
    "GDP per Capita PPP ($)": "gdp_pc_ppp",
    "GDP PPP ($)": "gdp_ppp",
    "Solar Share (%)": "solar_energy_share_pct",
    "Wind Share (%)": "wind_energy_share_pct",
    "Hydro Share (%)": "hydro_energy_share_pct",
    "Coal Share (%)": "coal_energy_share_pct",
}
feat_label = st.selectbox("Indicator", list(feature_options.keys()))
feat_col = feature_options[feat_label]

ranked_feat = rank_countries(df, year=year, sort_by=feat_col, ascending=False)
top10 = ranked_feat.head(10)

if top10.empty:
    st.info("No data available for this indicator and year.")
else:
    st.plotly_chart(make_top10_bar(top10, feat_col, feat_label, year), width="stretch")

# Keep filter_country imported if needed for inspection
_ = filter_country