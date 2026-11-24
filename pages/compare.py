from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from powering_planet.dataset import EnergyDataset
from powering_planet.metrics import ENERGY_GROUPS, iso3_to_flag
from powering_planet.plots import plot_stacked_energy

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    return EnergyDataset.load(DATA_PATH)


dataset = get_dataset()
st.title("⚖️ Head-to-Head Country Comparison")

# Sidebar controls
include_aggs = st.sidebar.checkbox("Include OWID regional aggregates", value=False)
countries = dataset.countries(include_aggregates=include_aggs)
valid_iso = dataset.df[["country", "iso_code"]].dropna()
iso_map = dict(zip(valid_iso["country"], valid_iso["iso_code"]))

col_a, col_b = st.sidebar.columns(2)
idx_a = countries.index("Italy") if "Italy" in countries else 0
idx_b = countries.index("Germany") if "Germany" in countries else min(1, len(countries) - 1)

country_a = col_a.selectbox(
    "Country A",
    countries,
    index=idx_a,
    format_func=lambda c: f"{iso3_to_flag(iso_map.get(c, ''))} {c}".strip(),
)
country_b = col_b.selectbox(
    "Country B",
    countries,
    index=idx_b,
    format_func=lambda c: f"{iso3_to_flag(iso_map.get(c, ''))} {c}".strip(),
)

if country_a == country_b:
    st.warning("Select two different countries in the sidebar for a head-to-head comparison.")

# Shared overlapping year range
full_a = dataset.get_country(country_a)
full_b = dataset.get_country(country_b)
min_y = int(max(full_a.df["year"].min(), full_b.df["year"].min()))
max_y = int(min(full_a.df["year"].max(), full_b.df["year"].max()))

years = st.sidebar.slider("Year Range", min_y, max_y, (max(min_y, max_y - 30), max_y))

prof_a = dataset.get_country(country_a, year_range=years)
prof_b = dataset.get_country(country_b, year_range=years)

flag_a = iso3_to_flag(prof_a.iso_code) or "🌍"
flag_b = iso3_to_flag(prof_b.iso_code) or "🌍"
label_a = f"{flag_a} {country_a}".strip()
label_b = f"{flag_b} {country_b}".strip()

st.subheader(f"{label_a}  vs.  {label_b}")

# --- 1. Side-by-Side KPI Snapshot ---
def _fmt_metric(val: float, unit: str = "", scale: float = 1.0, decimals: int = 1) -> str:
    if val is None or np.isnan(val):
        return "N/A"
    return f"{val / scale:,.{decimals}f}{unit}"


metrics_spec = [
    ("Total CO₂ (Mt)", "co2", " Mt", 1.0, 1),
    ("CO₂ per Capita (t)", "co2_per_capita", " t", 1.0, 2),
    ("Total Energy (TWh)", "total_energy_twh", " TWh", 1.0, 1),
    ("Low-Carbon Share (%)", "low_carbon_energy_share_pct", "%", 1.0, 1),
    ("Renewables Share (%)", "renewables_energy_share_pct", "%", 1.0, 1),
    ("GDP per Capita, PPP ($)", "gdp_pc_ppp", "", 1.0, 0),
]

k_left, k_right = st.columns(2)

with k_left:
    st.markdown(f"### {label_a}")
    dec_a = prof_a.decoupling_summary()
    st.caption(f"Decoupling status: **{dec_a['status']}**")
    cols_a = st.columns(2)
    for idx, (title, col_name, unit, scale, dec) in enumerate(metrics_spec):
        val, yr = prof_a.latest(col_name)
        cols_a[idx % 2].metric(f"{title} ({yr or 'N/A'})", _fmt_metric(val, unit, scale, dec))

with k_right:
    st.markdown(f"### {label_b}")
    dec_b = prof_b.decoupling_summary()
    st.caption(f"Decoupling status: **{dec_b['status']}**")
    cols_b = st.columns(2)
    for idx, (title, col_name, unit, scale, dec) in enumerate(metrics_spec):
        val, yr = prof_b.latest(col_name)
        cols_b[idx % 2].metric(f"{title} ({yr or 'N/A'})", _fmt_metric(val, unit, scale, dec))

st.divider()

# --- 2. Direct Trajectory Overlay Chart ---
st.subheader("📈 Trajectory Comparison Over Time")
trend_options = {
    "Low-Carbon Energy Share (%)": "low_carbon_energy_share_pct",
    "Renewables Energy Share (%)": "renewables_energy_share_pct",
    "CO₂ Emissions per Capita (t)": "co2_per_capita",
    "Total CO₂ Emissions (Mt)": "co2",
    "Total Primary Energy (TWh)": "total_energy_twh",
    "Carbon Intensity (Mt CO₂ / TWh)": "carbon_intensity_energy",
    "GDP per Capita, PPP ($)": "gdp_pc_ppp",
}
selected_label = st.selectbox("Select Indicator to Overlay", list(trend_options.keys()))
selected_col = trend_options[selected_label]

df_a = prof_a.df[["year", selected_col]].dropna().assign(Country=label_a)
df_b = prof_b.df[["year", selected_col]].dropna().assign(Country=label_b)
combined = pd.concat([df_a, df_b], ignore_index=True)

if combined.empty:
    st.info("No overlapping data available for this indicator.")
else:
    fig_trend = px.line(
        combined,
        x="year",
        y=selected_col,
        color="Country",
        markers=True,
        labels={"year": "Year", selected_col: selected_label},
        template="plotly_white",
    )
    fig_trend.update_layout(hovermode="x unified", legend_title_text="")
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- 3. Side-by-Side Primary Energy Mixes ---
st.subheader("⚡ Primary Energy Mix Breakdown")
mix_choice = st.radio(
    "Energy Mix View",
    options=["overview", "fossil", "low_carbon"],
    format_func=lambda k: {
        "overview": "Low Carbon vs. Fossil Fuels",
        "fossil": "Fossil Fuels by Source",
        "low_carbon": "Low-Carbon Energy by Source",
    }[k],
    horizontal=True,
)

total_map = {
    "overview": ("total_energy_twh", "Total consumption"),
    "fossil": ("fossil_fuels_energy_share_pct", "Reported fossil total"),
    "low_carbon": ("low_carbon_energy_share_pct", "Reported low-carbon total"),
}
tot_col, tot_lbl = total_map[mix_choice]

c_left, c_right = st.columns(2)
with c_left:
    st.markdown(f"**{label_a}**")
    st.plotly_chart(
        plot_stacked_energy(prof_a.df, ENERGY_GROUPS[mix_choice], total_col=tot_col, total_label=tot_lbl),
        use_container_width=True,
    )

with c_right:
    st.markdown(f"**{label_b}**")
    st.plotly_chart(
        plot_stacked_energy(prof_b.df, ENERGY_GROUPS[mix_choice], total_col=tot_col, total_label=tot_lbl),
        use_container_width=True,
    )