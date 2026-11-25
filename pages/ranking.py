from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from powering_planet.dataset import EnergyDataset
from powering_planet.metrics import iso3_to_flag

# Build the path to data/dataset.csv starting from this file's location (pages/ranking.py)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    """Load the dataset once and keep it cached so changing dropdowns or years is fast."""
    return EnergyDataset.load(DATA_PATH)


def _render_podium(ranked_df: pd.DataFrame, metric_col: str, title_prefix: str) -> None:
    """Show the top 3 countries side by side (1st, 2nd, 3rd) for a ranked table."""
    st.subheader(title_prefix)

    # Stop early with a friendly message if there is no data for the chosen filters
    if ranked_df.empty:
        st.info("No countries match the selected year for this metric.")
        return

    medals = {0: "🥇 1st", 1: "🥈 2nd", 2: "🥉 3rd"}

    # Grab up to the first 3 rows and place them in order from left to right (1st, 2nd, 3rd)
    top_rows = [ranked_df.iloc[i] for i in range(min(3, len(ranked_df)))]
    podium_order = list(range(len(top_rows)))
    podium_cols = st.columns(len(top_rows))

    for slot_idx, row_idx in enumerate(podium_order):
        row = top_rows[row_idx]
        flag = iso3_to_flag(row["iso_code"]) or "🌍"
        val = row[metric_col]

        # Format the number with 2 decimal places, or show "N/A" if the value is missing
        val_str = "N/A" if pd.isna(val) or np.isnan(val) else f"{val:,.2f}"

        with podium_cols[slot_idx]:
            st.markdown(f"#### {medals[row_idx]}")
            st.metric(label=f"{flag} {row['country']}".strip(), value=val_str)


dataset = get_dataset()
st.title("🏆 Country Ranking Page")

# Get all available years and default to 2025 (or the newest year if 2025 isn't present)
years = dataset.available_years()
default_year = 2025 if 2025 in years else years[-1]

# Put the Year dropdown in the left sidebar so it controls both sections below
year = st.sidebar.selectbox("Year", years, index=years.index(default_year))

# ---------------------------------------------------------------------------------------------------
# Section 1: Core Transition Ranking — rank countries using the 4 main energy transition metrics
st.divider()
st.header("Transition Ranking")

# Map dropdown labels to (column_name, sort_ascending):
# False = highest values come first (e.g. highest share of low-carbon energy)
# True  = lowest values come first (e.g. lowest carbon or energy intensity)
metric_options = {
    "Low-Carbon Energy Share (%)": ("low_carbon_energy_share_pct", False),
    "Renewables Energy Share (%)": ("renewables_energy_share_pct", False),
    "Lowest Carbon Intensity (Mt CO₂ / TWh)": ("carbon_intensity_energy", True),
    "Lowest Energy Intensity (TWh / $B GDP)": ("energy_intensity_gdp", True),
}
choice = st.selectbox("Rank By (Transition Metric)", list(metric_options.keys()), key="orig_rank_by")

col_name, ascending = metric_options[choice]

# Compute the full country ranking for the selected year and metric (min_population=0 includes all countries)
ranked_orig = dataset.ranking(
    year=year,
    sort_by=col_name,
    ascending=ascending,
    min_population=0,
)

# Display the 1st–3rd place podium above the full table
_render_podium(ranked_orig, col_name, f"Podium — {choice} ({year})")

# Pick which columns to show in the table and add a flag emoji next to each country name
display_cols = [
    "rank",
    "country",
    "iso_code",
    "low_carbon_energy_share_pct",
    "renewables_energy_share_pct",
    "carbon_intensity_energy",
    "co2_per_capita",
    "gdp_pc_ppp",
]
table_orig = ranked_orig[display_cols].copy()
table_orig["country"] = table_orig.apply(
    lambda r: f"{iso3_to_flag(r['iso_code'])} {r['country']}".strip(),
    axis=1,
)

# Show an interactive table filling the page width, without row numbers on the left
st.dataframe(table_orig, use_container_width=True, hide_index=True)

# Let the user download the table as a CSV file
st.download_button(
    label="Download Transition Ranking CSV",
    data=table_orig.to_csv(index=False).encode("utf-8"),
    file_name=f"powering_the_planet_transition_ranking_{year}.csv",
    mime="text/csv",
    key="dl_orig",
)

# ---------------------------------------------------------------------------------------------------
# Section 2: Top 10 horizontal bar chart — pick any individual feature to see the top 10 countries
st.divider()
st.header("Top 10 Countries by Feature")

# List of (raw_column_name, friendly_label) pairs, keeping only columns present in the dataset
feature_cols = [
    (col, label)
    for col, label in [
        ("population", "Population"),
        ("total_energy_twh", "Total Energy (TWh)"),
        ("coal_energy_share_pct", "Coal %"),
        ("oil_energy_share_pct", "Oil %"),
        ("gas_energy_share_pct", "Gas %"),
        ("nuclear_energy_share_pct", "Nuclear %"),
        ("hydro_energy_share_pct", "Hydro %"),
        ("wind_energy_share_pct", "Wind %"),
        ("solar_energy_share_pct", "Solar %"),
        ("biofuels_energy_share_pct", "Biofuels %"),
        ("other_renewables_including_bioenergy_energy_share_pct", "Other Renewables %"),
        ("co2", "CO₂ (Mt)"),
        ("co2_per_capita", "CO₂ / Capita (t)"),
        ("share_global_co2", "CO₂ global %"),
        ("gdp_pc_ppp", "GDP / Capita PPP ($)"),
        ("gdp_ppp", "GDP PPP ($)"),
    ]
    if col in dataset.df.columns
]

# Look up the raw column name from the friendly label chosen in the dropdown
feat_label_to_col = {label: col for col, label in feature_cols}
feat_choice = st.selectbox("Select Feature to Plot", list(feat_label_to_col.keys()), key="feat_rank_by")
feat_col = feat_label_to_col[feat_choice]

# Rank countries from highest to lowest for the chosen feature
ranked_feat = dataset.ranking(
    year=year,
    sort_by=feat_col,
    ascending=False,
    min_population=0,
)

# Keep only the top 10 rows for the bar chart
top10 = ranked_feat.head(10).copy()

if top10.empty:
    st.info("No countries match the selected year for this feature.")
else:
    # Build a label like "#1 🇳🇴 Norway" for each bar on the y-axis
    top10["country_label"] = top10.apply(
        lambda r: f"#{int(r['rank'])} {iso3_to_flag(r['iso_code'])} {r['country']}".strip(),
        axis=1,
    )

    # Create a horizontal bar chart ("h") with value labels printed next to each bar
    fig_top10 = px.bar(
        top10,
        x=feat_col,
        y="country_label",
        orientation="h",
        text=feat_col,
        color=feat_col,
        color_continuous_scale="Tealgrn",
        labels={feat_col: feat_choice, "country_label": ""},
        title=f"Top 10 Countries — {feat_choice} ({year})",
        template="plotly_white",
    )
    fig_top10.update_traces(texttemplate="%{text:,.2f}", textposition="outside")

    # Reverse the vertical axis so #1 appears at the top, and hide the redundant color legend bar
    fig_top10.update_layout(
        yaxis={"autorange": "reversed"},
        coloraxis_showscale=False,
        margin=dict(l=20, r=40, t=50, b=20),
        height=450,
    )
    st.plotly_chart(fig_top10, use_container_width=True)