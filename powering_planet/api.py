from pathlib import Path
import numpy as np
import streamlit as st
from powering_planet.dataset import EnergyDataset
from powering_planet.metrics import ENERGY_GROUPS, iso3_to_flag
from powering_planet.plots import plot_decoupling_index, plot_stacked_energy

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    """Cache the loaded EnergyDataset across Streamlit widget reruns."""
    return EnergyDataset.load(DATA_PATH)


dataset = get_dataset()

# Sidebar controls: aggregate toggle, country selector, and year range slider
include_aggs = st.sidebar.checkbox("Include OWID regional aggregates", value=False)
countries = dataset.countries(include_aggregates=include_aggs)
valid_iso = dataset.df[["country", "iso_code"]].dropna()
iso_map = dict(zip(valid_iso["country"], valid_iso["iso_code"]))

default_idx = countries.index("Italy") if "Italy" in countries else 0
country = st.sidebar.selectbox(
    "Select Country",
    countries,
    index=default_idx,
    format_func=lambda c: f"{iso3_to_flag(iso_map.get(c, ''))} {c}".strip(),
)

# Use full country history to set slider bounds, then slice to selected window
full_profile = dataset.get_country(country)
min_y, max_y = int(full_profile.df["year"].min()), int(full_profile.df["year"].max())
years = st.sidebar.slider("Year Range", min_y, max_y, (max(min_y, max_y - 30), max_y))

profile = dataset.get_country(country, year_range=years)
cdf = profile.df

flag = iso3_to_flag(profile.iso_code) or "🌍"
st.title(f"{flag} {profile.country} ({profile.iso_code})")

# Pull most recent non-null values and CAGR-based decoupling classification
co2_val, co2_yr = profile.latest("co2")
gdp_val, gdp_yr = profile.latest("gdp_ppp")
eng_val, eng_yr = profile.latest("total_energy_twh")
decoupling = profile.decoupling_summary()

# Top 4-column KPI summary row
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Total CO₂ ({co2_yr or 'N/A'})", f"{co2_val:,.1f} Mt" if not np.isnan(co2_val) else "N/A")
k2.metric(f"Total GDP, PPP ({gdp_yr or 'N/A'})", f"${gdp_val / 1e9:,.1f} B" if not np.isnan(gdp_val) else "N/A")
k3.metric(f"Total Energy ({eng_yr or 'N/A'})", f"{eng_val:,.1f} TWh" if not np.isnan(eng_val) else "N/A")
k4.metric(
    "Growth vs. Emissions",
    decoupling["status"],
    delta=f"CO₂ {decoupling['co2_cagr']:+.1f}%/yr" if not np.isnan(decoupling["co2_cagr"]) else None,
    delta_color="inverse",  # Negative CO2 growth (emissions drop) is shown as favorable
)

st.divider()

# Stacked area energy mix charts: high-level split, fossil breakdown, and low-carbon breakdown
st.subheader(f"{flag} Low Carbon vs. Fossil Fuels")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["overview"], total_col="total_energy_twh", total_label="Total consumption"),
    use_container_width=True,
)

st.subheader(f"{flag} Fossil Fuel Consumption by Source")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["fossil"], total_col="fossil_fuels_energy_share_pct", total_label="Reported fossil total"),
    use_container_width=True,
)

st.subheader(f"{flag} Low-Carbon Energy by Source")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["low_carbon"], total_col="low_carbon_energy_share_pct", total_label="Reported low-carbon total"),
    use_container_width=True,
)

st.divider()
st.subheader(f"{flag} Growth vs. Energy vs. Emissions (Indexed)")

# Guard against empty/single-row slices before drawing the rebased index chart
if len(cdf[["year", "gdp_ppp", "total_energy_twh", "co2", "co2_per_capita"]].dropna()) >= 2:
    st.plotly_chart(plot_decoupling_index(cdf), use_container_width=True)
else:
    st.info("Not enough overlapping years for the decoupling chart.")

st.divider()

# ---------------------------------------------------------------------------------------------------
# Country data table using the pipeline columns from api.py
st.subheader(f"{flag} {profile.country} Data Table ({years[0]}–{years[1]})")

api_table_cols = [
    c
    for c in [
        "year",
        "country",
        "iso_code",
        "population",
        "total_energy_twh",
        "fossil_fuels_energy_share_pct",
        "coal_energy_share_pct",
        "oil_energy_share_pct",
        "gas_energy_share_pct",
        "low_carbon_energy_share_pct",
        "renewables_energy_share_pct",
        "nuclear_energy_share_pct",
        "hydro_energy_share_pct",
        "wind_energy_share_pct",
        "solar_energy_share_pct",
        "biofuels_energy_share_pct",
        "other_renewables_including_bioenergy_energy_share_pct",
        "co2",
        "co2_per_capita",
        "share_global_co2",
        "gdp_pc_ppp",
        "gdp_ppp",
    ]
    if c in cdf.columns
]

country_table = cdf[api_table_cols].sort_values("year", ascending=False).reset_index(drop=True)
st.dataframe(country_table, use_container_width=True, hide_index=True)
    