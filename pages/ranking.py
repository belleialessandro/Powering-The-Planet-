"""Country ranking page: leaderboard, podium, CSV download, Top 10, and scatter."""

import os
import numpy as np
import pandas as pd
import streamlit as st
from powering_planet import config as c
from powering_planet import dataset as d
from powering_planet import plots as p


@st.cache_data
def cached_load_data(path):
    """Load the dataset once and cache it across interactions."""
    return d.load_data(path)


data_file = os.path.join(os.path.dirname(__file__), "..", d.DEFAULT_DATA_PATH)
df = cached_load_data(data_file)

st.title("Country Ranking")

all_years = sorted(df["year"].dropna().astype(int).unique().tolist())
default_year = 2024 if 2024 in all_years else all_years[-1]
year = st.sidebar.selectbox("Year", all_years, index=all_years.index(default_year))

st.divider()
st.subheader("Transition Ranking")

metric_label = st.selectbox("Rank by", list(c.METRIC_OPTIONS.keys()))
sort_col, ascending = c.METRIC_OPTIONS[metric_label]

ranked = d.rank_countries(df, year=year, sort_by=sort_col, ascending=ascending)

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

feat_label = st.selectbox("Indicator", list(c.FEATURE_OPTIONS.keys()))
feat_col = c.FEATURE_OPTIONS[feat_label]

ranked_feat = d.rank_countries(df, year=year, sort_by=feat_col, ascending=False)
top10 = ranked_feat.head(10)

if top10.empty:
    st.info("No data available for this indicator and year.")
else:
    st.plotly_chart(p.make_top10_bar(top10, feat_col, feat_label, year), width="stretch")

st.divider()
st.subheader("Country Scatter Plot")

year_df = d.rank_countries(df, year=year, sort_by=feat_col, ascending=False)
available_countries = d.get_countries(year_df)

col_x, col_y, col_z = st.columns(3)
x_label = col_x.selectbox("X-axis feature", list(c.FEATURE_OPTIONS.keys()), index=3)
y_label = col_y.selectbox("Y-axis feature", list(c.FEATURE_OPTIONS.keys()), index=2)
z_label = col_z.selectbox("Color feature", list(c.FEATURE_OPTIONS.keys()), index=1)

selected_countries = st.multiselect(
    "Filter countries (leave empty to show all countries)",
    options=available_countries,
    default=[],
)

scatter_df = year_df
if selected_countries:
    scatter_df = year_df[year_df["country"].isin(selected_countries)]

scatter_fig = p.make_feature_scatter(
    scatter_df,
    c.FEATURE_OPTIONS[x_label],
    x_label,
    c.FEATURE_OPTIONS[y_label],
    y_label,
    c.FEATURE_OPTIONS[z_label],
    z_label,
    year,
)
if scatter_fig is None:
    st.info("No data available for the selected features, countries, and year.")
else:
    st.plotly_chart(scatter_fig, width="stretch")

# Keep filter_country imported if needed for inspection
_ = d.filter_country