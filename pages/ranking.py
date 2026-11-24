from pathlib import Path
import streamlit as st
from powering_planet.dataset import EnergyDataset

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    return EnergyDataset.load(DATA_PATH)


dataset = get_dataset()
st.title("🏆 Global Energy Transition Ranking")

years = dataset.available_years()
default_year = 2022 if 2022 in years else years[-1]

c1, c2, c3 = st.columns(3)
year = c1.selectbox("Year", years, index=years.index(default_year))
metric_options = {
    "Low-Carbon Energy Share (%)": ("low_carbon_energy_share_pct", False),
    "Renewables Energy Share (%)": ("renewables_energy_share_pct", False),
    "Lowest Carbon Intensity (Mt CO₂ / TWh)": ("carbon_intensity_energy", True),
    "Lowest Energy Intensity (TWh / $B GDP)": ("energy_intensity_gdp", True),
}
choice = c2.selectbox("Rank By", list(metric_options.keys()))
min_pop_m = c3.slider("Minimum Population (Millions)", 0, 50, 5)

col_name, ascending = metric_options[choice]
ranked = dataset.ranking(year=year, sort_by=col_name, ascending=ascending, min_population=min_pop_m * 1e6)

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
table = ranked[display_cols].copy()

st.dataframe(table, use_container_width=True, hide_index=True)

st.download_button(
    label="Download Ranking CSV",
    data=table.to_csv(index=False).encode("utf-8"),
    file_name=f"powering_the_planet_ranking_{year}.csv",
    mime="text/csv",
)