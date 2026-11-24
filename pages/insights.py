from pathlib import Path
import streamlit as st
from powering_planet.analysis import gdp_co2_correlation, simulate_transition
from powering_planet.dataset import EnergyDataset
from powering_planet.metrics import iso3_to_flag
from powering_planet.plots import plot_kuznets_scatter

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    return EnergyDataset.load(DATA_PATH)


dataset = get_dataset()
st.title("📊 Cross-Country Insights & Decarbonization Simulator")

years = dataset.available_years()
default_year = 2022 if 2022 in years else years[-1]
year = st.selectbox("Snapshot Year", years, index=years.index(default_year))

corr = gdp_co2_correlation(dataset.df, year)
m1, m2, m3 = st.columns(3)
m1.metric("Countries Compared", corr["n"])
m2.metric("Spearman ρ (GDP pc vs CO₂ pc)", f"{corr['spearman_r']:.2f}")
m3.metric("Log-Linear Pearson r", f"{corr['pearson_r']:.2f}")

st.plotly_chart(plot_kuznets_scatter(dataset.df, year), use_container_width=True)

st.divider()
st.subheader("⚡ What-If Fossil Phase-Out Simulator")

countries = dataset.countries()
valid_iso = dataset.df[["country", "iso_code"]].dropna()
iso_map = dict(zip(valid_iso["country"], valid_iso["iso_code"]))

sim_country = st.selectbox(
    "Target Country",
    countries,
    index=countries.index("Italy") if "Italy" in countries else 0,
    format_func=lambda c: f"{iso3_to_flag(iso_map.get(c, ''))} {c}".strip(),
)
profile = dataset.get_country(sim_country)
valid_rows = profile.df.dropna(subset=["total_energy_twh", "co2"])

if valid_rows.empty:
    st.warning("No complete energy and CO₂ data available for this country.")
else:
    latest_row = valid_rows.iloc[-1]
    st.caption(
        f"Baseline year: **{int(latest_row['year'])}** | "
        f"Coal share: **{latest_row['coal_energy_share_pct']:.1f}%** | "
        f"Gas share: **{latest_row['gas_energy_share_pct']:.1f}%**"
    )

    s1, s2 = st.columns(2)
    coal_cut = s1.slider("Replace Coal Share with Zero-Carbon (%)", 0, 100, 50)
    gas_cut = s2.slider("Replace Gas Share with Zero-Carbon (%)", 0, 100, 25)

    res = simulate_transition(latest_row, coal_cut_pct=coal_cut, gas_cut_pct=gas_cut)

    r1, r2, r3 = st.columns(3)
    r1.metric("Baseline CO₂", f"{res['baseline_co2_mt']:,.1f} Mt")
    r2.metric("Projected CO₂", f"{res['new_co2_mt']:,.1f} Mt", delta=f"-{res['saved_co2_mt']:,.1f} Mt", delta_color="inverse")
    r3.metric("Total Emissions Cut", f"{res['reduction_pct']:.1f}%")