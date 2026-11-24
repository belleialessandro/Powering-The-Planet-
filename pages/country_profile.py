from pathlib import Path
import numpy as np
import streamlit as st
from powering_planet.dataset import EnergyDataset
from powering_planet.metrics import ENERGY_GROUPS, iso3_to_flag
from powering_planet.plots import plot_decoupling_index, plot_stacked_energy

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    return EnergyDataset.load(DATA_PATH)


dataset = get_dataset()

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

full_profile = dataset.get_country(country)
min_y, max_y = int(full_profile.df["year"].min()), int(full_profile.df["year"].max())
years = st.sidebar.slider("Year Range", min_y, max_y, (max(min_y, max_y - 30), max_y))

profile = dataset.get_country(country, year_range=years)
cdf = profile.df

flag = iso3_to_flag(profile.iso_code) or "🌍"
st.title(f"{flag} {profile.country} ({profile.iso_code})")

co2_val, co2_yr = profile.latest("co2")
gdp_val, gdp_yr = profile.latest("gdp_ppp")
eng_val, eng_yr = profile.latest("total_energy_twh")
decoupling = profile.decoupling_summary()

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Total CO₂ ({co2_yr or 'N/A'})", f"{co2_val:,.1f} Mt" if not np.isnan(co2_val) else "N/A")
k2.metric(f"Total GDP, PPP ({gdp_yr or 'N/A'})", f"${gdp_val / 1e9:,.1f} B" if not np.isnan(gdp_val) else "N/A")
k3.metric(f"Total Energy ({eng_yr or 'N/A'})", f"{eng_val:,.1f} TWh" if not np.isnan(eng_val) else "N/A")
k4.metric(
    "Growth vs. Emissions",
    decoupling["status"],
    delta=f"CO₂ {decoupling['co2_cagr']:+.1f}%/yr" if not np.isnan(decoupling["co2_cagr"]) else None,
    delta_color="inverse",
)

st.divider()

st.subheader(f"{country}: Low Carbon vs. Fossil Fuels")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["overview"], total_col="total_energy_twh", total_label="Total consumption"),
    use_container_width=True,
)

st.subheader(f"{country}: Fossil Fuel Consumption by Source")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["fossil"], total_col="fossil_fuels_energy_share_pct", total_label="Reported fossil total"),
    use_container_width=True,
)

st.subheader(f"{country}: Low-Carbon Energy by Source")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["low_carbon"], total_col="low_carbon_energy_share_pct", total_label="Reported low-carbon total"),
    use_container_width=True,
)

st.divider()
st.subheader(f"{country}: Growth vs. Energy vs. Emissions (Indexed)")
if len(cdf[["year", "gdp_ppp", "total_energy_twh", "co2", "co2_per_capita"]].dropna()) >= 2:
    st.plotly_chart(plot_decoupling_index(cdf), use_container_width=True)
else:
    st.info("Not enough overlapping years for the decoupling chart.")