from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
from powering_planet.analysis import simulate_transition
from powering_planet.dataset import EnergyDataset
from powering_planet.metrics import ENERGY_GROUPS, iso3_to_flag
from powering_planet.plots import plot_decoupling_index, plot_stacked_energy

# Find the path to data/dataset.csv relative to this file (pages/country_profile.py -> project root -> data/dataset.csv)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"


@st.cache_data
def get_dataset() -> EnergyDataset:
    """Load the dataset once and keep it in memory so the app stays fast when sliders or dropdowns change."""
    return EnergyDataset.load(DATA_PATH)


dataset = get_dataset()

# ---------------------------------------------------------------------------------------------------
# Sidebar controls: let the user pick whether to include regional/world totals, which country to view,
# and which range of years to look at

# Checkbox in the left sidebar, unchecked by default
include_aggs = st.sidebar.checkbox("Include OWID regional aggregates", value=False)
countries = dataset.countries(include_aggregates=include_aggs)

# Build a lookup table (dictionary) mapping each country name to its 3-letter code so we can show flag emojis
valid_iso = dataset.df[["country", "iso_code"]].dropna()
iso_map = dict(zip(valid_iso["country"], valid_iso["iso_code"]))

# Pick "Italy" as the starting country if it exists in the list, otherwise pick the first item
default_idx = countries.index("Italy") if "Italy" in countries else 0
country = st.sidebar.selectbox(
    "Select Country",
    countries,
    index=default_idx,
    format_func=lambda c: f"{iso3_to_flag(iso_map.get(c, ''))} {c}".strip(),
)

# Look up the full history for this country first to find its earliest and latest available years
full_profile = dataset.get_country(country)
min_y, max_y = int(full_profile.df["year"].min()), int(full_profile.df["year"].max())

# Slider in the sidebar to filter the years; defaults to roughly the last 30 years up to the latest year
years = st.sidebar.slider("Year Range", min_y, max_y, (max(min_y, max_y - 30), max_y))

# Create the filtered country data for just the selected year range
profile = dataset.get_country(country, year_range=years)
cdf = profile.df  # Short name ("country dataframe") for the filtered table of rows

# Turn the country code into a flag emoji (falling back to a globe if no flag applies) and show the page title
flag = iso3_to_flag(profile.iso_code) or "🌍"
st.title(f"{flag} {profile.country} ({profile.iso_code})")

# ---------------------------------------------------------------------------------------------------
# Top summary KPI... show the most recent available figures and how emissions grew and the economy

# Get the newest not empty value and its year for CO2, GDP, and total energy
co2_val, co2_yr = profile.latest("co2")
gdp_val, gdp_yr = profile.latest("gdp_ppp")
eng_val, eng_yr = profile.latest("total_energy_twh")

# Check whether the economy grew while emissions dropped or grew slower ("decoupling")
decoupling = profile.decoupling_summary()

# Create 4 side by side boxes; the 4th box is slightly wider (1.3 vs 1) to fit its label comfortably
k1, k2, k3, k4 = st.columns([1, 1, 1, 1.3])
k1.metric(f"Total CO₂ ({co2_yr or 'N/A'})", f"{co2_val:,.1f} Mt" if not np.isnan(co2_val) else "N/A")
k2.metric(f"Total GDP PPP ({gdp_yr or 'N/A'})", f"${gdp_val / 1e9:,.1f} B" if not np.isnan(gdp_val) else "N/A")
k3.metric(f"Total Energy ({eng_yr or 'N/A'})", f"{eng_val:,.1f} TWh" if not np.isnan(eng_val) else "N/A")

# Remove " Decoupling" so the big KPI text stays short and doesn't get cut off with "..."
short_status = decoupling["status"].replace(" Decoupling", "")
k4.metric(
    "Decoupling Status",
    short_status,
    # Put the +/- sign first so Streamlit colors a drop in CO2 as positive/good (green) and a rise as red
    delta=f"{decoupling['co2_cagr']:+.1f}%/yr CO₂" if not np.isnan(decoupling["co2_cagr"]) else None,
    delta_color="inverse",
)

st.divider()

# ---------------------------------------------------------------------------------------------------
# Energy mix charts: stacked area charts showing how much energy comes from each source over time
# (each chart spans the full width of the page)

# Chart 1: Big-picture split between fossil fuels and low-carbon energy, with a line for total energy
st.subheader(f"{flag} Low Carbon vs. Fossil Fuels")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["overview"], total_col="total_energy_twh", total_label="Total consumption"),
    use_container_width=True,
)

# Chart 2: Breakdown of fossil fuels into coal, oil, and gas
st.subheader(f"{flag} Fossil Fuel Consumption by Source")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["fossil"], total_col="fossil_fuels_energy_share_pct", total_label="Reported fossil total"),
    use_container_width=True,
)

# Chart 3: Breakdown of low-carbon sources (nuclear, hydro, wind, solar, biofuels, other renewables)
st.subheader(f"{flag} Low-Carbon Energy by Source")
st.plotly_chart(
    plot_stacked_energy(cdf, ENERGY_GROUPS["low_carbon"], total_col="low_carbon_energy_share_pct", total_label="Reported low-carbon total"),
    use_container_width=True,
)

st.divider()
st.subheader(f"{flag} Growth vs. Energy vs. Emissions (Indexed)")

# Only draw the indexed comparison chart if there are at least 2 complete years to compare from start to end
if len(cdf[["year", "gdp_ppp", "total_energy_twh", "co2", "co2_per_capita"]].dropna()) >= 2:
    st.plotly_chart(plot_decoupling_index(cdf), use_container_width=True)
else:
    st.info("Not enough overlapping years for the decoupling chart.")

st.divider()

# ---------------------------------------------------------------------------------------------------
# Interactive "What-If" simulator: test replacing shares of coal, oil, and gas with zero-carbon energy
# using the most recent complete year in the selected country's data
st.subheader(f"{flag} What-If Fossil Phase-Out Simulator")

valid_rows = cdf.dropna(subset=["total_energy_twh", "co2"])

if valid_rows.empty:
    st.warning("No complete energy and CO₂ data available for this country in the selected year range.")
else:
    # Pick the latest row with valid energy and CO2 figures as the starting baseline
    latest_row = valid_rows.iloc[-1]

    coal_share = latest_row.get("coal_energy_share_pct", float("nan"))
    oil_share = latest_row.get("oil_energy_share_pct", float("nan"))
    gas_share = latest_row.get("gas_energy_share_pct", float("nan"))

    coal_text = f"**{coal_share:.1f}%**" if pd.notna(coal_share) else "**N/A**"
    oil_text = f"**{oil_share:.1f}%**" if pd.notna(oil_share) else "**N/A**"
    gas_text = f"**{gas_share:.1f}%**" if pd.notna(gas_share) else "**N/A**"

    st.caption(
        f"Baseline year: **{int(latest_row['year'])}** | "
        f"Coal share: {coal_text} | "
        f"Oil share: {oil_text} | "
        f"Gas share: {gas_text}"
    )

    # Three side-by-side sliders: percentage of coal, oil, and gas replaced by zero-carbon energy
    s1, s2, s3 = st.columns(3)
    coal_cut = s1.slider("Replace Coal Share with Zero-Carbon (%)", 0, 100, 50, key="sim_coal_cut")
    oil_cut = s2.slider("Replace Oil Share with Zero-Carbon (%)", 0, 100, 25, key="sim_oil_cut")
    gas_cut = s3.slider("Replace Gas Share with Zero-Carbon (%)", 0, 100, 25, key="sim_gas_cut")

    # Estimate resulting CO2 emissions and total savings
    res = simulate_transition(
        latest_row,
        coal_cut_pct=coal_cut,
        oil_cut_pct=oil_cut,
        gas_cut_pct=gas_cut,
    )

    # Show baseline emissions, projected emissions (with saved Mt badge), and percentage cut
    r1, r2, r3 = st.columns(3)
    r1.metric("Baseline CO₂", f"{res['baseline_co2_mt']:,.1f} Mt")
    r2.metric(
        "Projected CO₂",
        f"{res['new_co2_mt']:,.1f} Mt",
        delta=f"-{res['saved_co2_mt']:,.1f} Mt",
        delta_color="inverse",
    )
    r3.metric("Total Emissions Cut", f"{res['reduction_pct']:.1f}%")

st.divider()

# ---------------------------------------------------------------------------------------------------
# Detailed data table: shows the underlying numbers year by year for the selected country and years

st.subheader(f"{flag} {profile.country} Data Table ({years[0]}–{years[1]})")

# List of (raw dataset column name, friendly table header) pairs.
# Aggregate totals like fossil/renewables/low-carbon shares are left out because they can be summed
# from the individual sources, and we only keep columns that actually exist in cdf.
api_table_cols = [
    (col, label)
    for col, label in [
        ("year", "Year"),
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
    if col in cdf.columns
]

# Separate the raw column names (to select data) from the friendly names (to label the table headers)
raw_cols = [col for col, _ in api_table_cols]
rename_map = dict(api_table_cols)

# Put the most recent years at the top, apply friendly column names, reset row numbers, and display the table
country_table = (
    cdf[raw_cols]
    .sort_values("year", ascending=False)
    .rename(columns=rename_map)
    .reset_index(drop=True)
)
st.dataframe(country_table, use_container_width=True, hide_index=True)