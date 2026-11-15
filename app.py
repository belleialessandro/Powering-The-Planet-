# Powering the Planet: Streamlit dashboard on energy, emissions and growth
# Run with: streamlit run app.py

# Path lets us build file paths that work on Windows, macOS and Linux
from pathlib import Path
# pyplot is matplotlib's main drawing interface (figures, axes, plots)
import matplotlib.pyplot as plt
# ticker controls how axis numbers are formatted and how many ticks appear
import matplotlib.ticker as ticker
# numpy handles fast array math (sums, maxima, NaN checks)
import numpy as np
# pandas handles the table of data (DataFrames)
import pandas as pd
# streamlit turns this script into a web app (widgets, text, charts)
import streamlit as st

# Page setup. This must be the first Streamlit command in the script.
# page_title and page_icon: text and emoji shown in the browser tab
# layout="wide": use the full browser width instead of a narrow centered column
st.set_page_config(page_title="Powering the Planet", page_icon="🌍", layout="wide")

# Absolute path to the CSV: __file__ is this script, .resolve() makes the path absolute,
# .parent is the folder containing it, then we go into data/dataset.csv.
# This way the app works no matter which folder you launch it from.
DATA_PATH = Path(__file__).resolve().parent / "data" / "dataset.csv"

# Columns the energy charts need. We use this list below to check
# that the CSV really contains all of them before drawing anything.
SELECTED_ENERGY_COLS = [
    "country",                                                # country name
    "iso_code",                                               # 3-letter country code (e.g. ITA)
    "population",                                             # number of inhabitants
    "year",                                                   # year of the observation
    "solar_energy_share_pct",                                 # % of total energy from solar
    "wind_energy_share_pct",                                  # % from wind
    "hydro_energy_share_pct",                                 # % from hydropower
    "biofuels_energy_share_pct",                              # % from biofuels
    "other_renewables_including_bioenergy_energy_share_pct",  # % from other renewables
    "nuclear_energy_share_pct",                               # % from nuclear
    "oil_energy_share_pct",                                   # % from oil
    "gas_energy_share_pct",                                   # % from natural gas
    "coal_energy_share_pct",                                  # % from coal
    "fossil_fuels_energy_share_pct",                          # % from coal + oil + gas combined
    "renewables_energy_share_pct",                            # % from all renewables combined
    "low_carbon_energy_share_pct",                            # % from renewables + nuclear
    "total_energy_twh",                                       # total primary energy, in TWh
]


# Data loading

# Cache the result so the CSV is read once, not on every rerun of the app
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    # Read the CSV, sort by country then year (so the last row of a country is
    # its latest year), and renumber the rows from 0 after sorting
    return pd.read_csv(path).sort_values(["country", "year"]).reset_index(drop=True)


# If the CSV doesn't exist, show a red error box and stop the script here
if not DATA_PATH.exists():
    st.error(f"Dataset not found at `{DATA_PATH}`.")
    st.stop()  # nothing below this line runs

# Load the whole dataset into a DataFrame (all countries, all years)
df = load_data(DATA_PATH)

# Build a list of required columns that are NOT in the CSV
missing_cols = [c for c in SELECTED_ENERGY_COLS if c not in df.columns]
# If that list isn't empty, tell the user which ones are missing and stop
if missing_cols:
    st.error(f"Missing columns in dataset: {missing_cols}")
    st.stop()


# Sidebar: country and year-range filters

# Alphabetical list of unique country names (dropna removes empty values)
countries = sorted(df["country"].dropna().unique())
# Position of "Italy" in that list, so the dropdown starts on Italy (0 = first country if no Italy)
default_idx = countries.index("Italy") if "Italy" in countries else 0
# Dropdown in the sidebar; `country` holds whatever the user picks
country = st.sidebar.selectbox("Select Country", countries, index=default_idx)

# Keep only the rows of the selected country; .copy() avoids pandas warnings when we filter again
cdf = df[df["country"] == country].copy()

# First and last year available for this country (converted to plain ints)
min_y, max_y = int(cdf["year"].min()), int(cdf["year"].max())
# Default start of the slider = 30 years before the last year (but never before the first year)
default_start = max(min_y, max_y - 30)
# Two-handle slider in the sidebar; returns a (start_year, end_year) tuple
years = st.sidebar.slider("Year Range", min_y, max_y, (default_start, max_y))
# Keep only the rows whose year is inside the chosen range (inclusive on both ends)
cdf = cdf[cdf["year"].between(years[0], years[1])]


def latest_value(data: pd.DataFrame, col: str):
    """Return (value, year) of the most recent non-null entry in `col`."""
    # Keep only year + the column, and drop rows where the column is empty
    valid = data[["year", col]].dropna()
    # If nothing is left, there is no value to show
    if valid.empty:
        return np.nan, None
    # Data is sorted by year, so the last row is the latest available year
    last_row = valid.iloc[-1]
    # Return the value and its year
    return last_row[col], int(last_row["year"])


# Header and KPI tiles (latest available value for each metric)

# 3-letter code of the selected country (the first row is enough, they are all the same); "" if no data
iso = cdf["iso_code"].iloc[0] if not cdf.empty else ""
# Big page title, e.g. "🌍 Italy (ITA)"
st.title(f"🌍 {country} ({iso})")

# Latest CO2 emissions, GDP and total energy, each with the year it refers to
co2_val, co2_yr = latest_value(cdf, "co2")
gdp_val, gdp_yr = latest_value(cdf, "gdp_ppp")
eng_val, eng_yr = latest_value(cdf, "total_energy_twh")

# Create three side-by-side columns, one per KPI tile
k1, k2, k3 = st.columns(3)
# Tile 1: label includes the year (or "N/A"); value has 1 decimal and thousands separators
k1.metric(
    f"Total CO₂ ({co2_yr or 'N/A'})",
    f"{co2_val:,.1f} Mt" if not np.isnan(co2_val) else "N/A",
)
# Tile 2: GDP divided by 1e9 so it is shown in billions of dollars
k2.metric(
    f"Total GDP, PPP ({gdp_yr or 'N/A'})",
    f"${gdp_val / 1e9:,.1f} B" if not np.isnan(gdp_val) else "N/A",
)
# Tile 3: total energy consumption in TWh
k3.metric(
    f"Total Energy Consumed ({eng_yr or 'N/A'})",
    f"{eng_val:,.1f} TWh" if not np.isnan(eng_val) else "N/A",
)

# Thin horizontal line separating the KPIs from the charts
st.divider()


# Helpers for the stacked time-series charts

def to_twh(data: pd.DataFrame, share_col: str) -> np.ndarray:
    """Convert a '% of total energy' column into TWh (missing values count as 0)."""
    # TWh of a source = total energy x its percentage share / 100.
    # fillna(0.0) turns missing shares into 0; .to_numpy() returns a plain array for matplotlib.
    return (data["total_energy_twh"] * data[share_col].fillna(0.0) / 100.0).to_numpy()


def stacked_area_chart(data, components, total_col=None, total_label=None, height=4.5):
    """
    Draw a stacked area chart in TWh, with an optional dark "total" line on top.

    data       : DataFrame with year, total_energy_twh and the share columns
    components : list of (share_col, label, color), stacked bottom to top
    total_col  : optional column drawn as a dark line. Either a share column
                 (converted to TWh) or "total_energy_twh" (already in TWh).
    total_label: legend text for the dark line
    """
    # Years go on the horizontal axis
    x = data["year"].to_numpy()
    # One TWh series per component (the "_" ignores the label and color in each tuple)
    layers = [to_twh(data, c) for c, _, _ in components]
    # Legend names, in the same order as the layers
    labels = [l for _, l, _ in components]
    # Fill colors, in the same order as the layers
    colors = [col for _, _, col in components]

    # Create the figure (canvas) and axes (the plotting area); size is in inches, dpi = sharpness
    fig, ax = plt.subplots(figsize=(11, height), dpi=130)

    # Draw the stacked bands. alpha=0.85 makes colors slightly soft;
    # linewidth=0 removes outlines between bands for a smooth look
    ax.stackplot(x, layers, labels=labels, colors=colors, alpha=0.85, linewidth=0)

    # Height of the stack for each year (sum of all bands); used to set the y-axis limit later
    top = np.sum(layers, axis=0)
    # Only draw the dark line if a total column was requested
    if total_col is not None:
        # "total_energy_twh" is already in TWh, so use it directly
        if total_col == "total_energy_twh":
            total_line = data["total_energy_twh"].to_numpy()
        # Any other column is a % share, so convert it to TWh first
        else:
            total_line = to_twh(data, total_col)
        # Dark line = reported total; it should sit on top of the stack if the parts add up
        ax.plot(x, total_line, color="#222222", linewidth=1.6, label=total_label)
        # Per-year maximum of stack and line, so the y-axis fits whichever is taller
        top = np.maximum(top, total_line)

    # Horizontal axis spans exactly from the first to the last year (no empty margins)
    ax.set_xlim(x.min(), x.max())
    # Vertical axis from 0 to the highest value plus 5% headroom
    ax.set_ylim(0, top.max() * 1.05)
    # Y-axis title
    ax.set_ylabel("Primary energy (TWh)", fontsize=9, color="#444444")
    # Show y numbers with thousands separators and no decimals (e.g. 2,500)
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    # Up to about 10 x ticks, forced to whole numbers so years never show as 2010.5
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
    # Tick label size and color on both axes
    ax.tick_params(labelsize=9, colors="#444444")

    # Light horizontal grid lines only
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    # Put the grid behind the data instead of on top of it
    ax.set_axisbelow(True)
    # Hide the top, right and left frame lines for a cleaner look
    ax.spines[["top", "right", "left"]].set_visible(False)
    # Keep the bottom line, in soft gray
    ax.spines["bottom"].set_color("#888888")

    # Legend centered below the plot; ncol puts all entries on one row
    # (one extra column when the dark total line adds another entry)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),  # x = middle, y = slightly below the axes
        ncol=len(labels) + (1 if total_col else 0),
        frameon=False,  # no box around the legend
        fontsize=9,
    )

    # Adjust margins so labels and the legend aren't cut off
    fig.tight_layout()
    # Display the figure in the Streamlit page
    st.pyplot(fig)
    # Close the figure to free memory; Streamlit reruns create many figures
    plt.close(fig)


def prepare(data: pd.DataFrame, share_cols: list) -> pd.DataFrame:
    """Keep rows with a total and at least one non-null share."""
    # Select year, total energy and the needed share columns; drop years with no total energy
    out = data[["year", "total_energy_twh"] + share_cols].dropna(subset=["total_energy_twh"])
    # Also drop years where ALL share columns are empty, then renumber rows from 0
    return out.dropna(how="all", subset=share_cols).reset_index(drop=True)


# Graph 1: Total energy = Low carbon + Fossil fuels

# Section heading with the selected country's name
st.subheader(f"{country}: Total Energy Consumption — Low Carbon vs. Fossil Fuels")

# Bands for graph 1: (column, legend label, color), bottom to top
g1_components = [
    ("fossil_fuels_energy_share_pct", "Fossil fuels", "#6b4f4a"),  # bottom band, brown
    ("low_carbon_energy_share_pct", "Low carbon", "#2a9d8f"),      # top band, teal
]
# Clean data for this chart (only the two share columns are needed)
g1 = prepare(cdf, [c for c, _, _ in g1_components])

# An area chart needs at least two points, otherwise show an info message
if len(g1) < 2:
    st.info("Not enough data for this chart (need at least 2 years).")
else:
    # The dark line is total consumption; if the stack doesn't reach it,
    # part of the energy is classified as neither fossil nor low carbon
    stacked_area_chart(
        g1, g1_components, total_col="total_energy_twh", total_label="Total energy consumption"
    )
    # Small explanatory text under the chart
    st.caption(
        "Band thickness = TWh of primary energy. The dark line is total consumption; "
        "if the bands don't reach it, part of the energy isn't classified as fossil or low carbon."
    )


# Graph 2: Fossil fuels = Coal + Oil + Gas

st.subheader(f"{country}: Fossil Fuel Consumption by Source")

# Bands for graph 2, bottom to top: coal, then oil, then gas
g2_components = [
    ("coal_energy_share_pct", "Coal", "#4a4a4a"),
    ("oil_energy_share_pct", "Oil", "#c65d6e"),
    ("gas_energy_share_pct", "Gas", "#83589c"),
]
# Include the reported fossil share so `prepare` keeps it and the dark line can use it
g2_cols = [c for c, _, _ in g2_components] + ["fossil_fuels_energy_share_pct"]
g2 = prepare(cdf, g2_cols)

if len(g2) < 2:
    st.info("Not enough data for this chart (need at least 2 years).")
else:
    # The dark line is the reported fossil total; the three bands should reach it
    stacked_area_chart(
        g2, g2_components, total_col="fossil_fuels_energy_share_pct", total_label="Reported fossil total"
    )


# Graph 3: Low carbon = Nuclear + Hydro + Wind + Solar + Biofuels + Other renewables

st.subheader(f"{country}: Low-Carbon Energy by Source")

# Bands for graph 3, bottom to top
g3_components = [
    ("nuclear_energy_share_pct", "Nuclear", "#238b7e"),  # part of "low carbon", not "renewables"
    ("hydro_energy_share_pct", "Hydro", "#1d78b5"),
    ("wind_energy_share_pct", "Wind", "#1d3557"),
    ("solar_energy_share_pct", "Solar", "#f2a541"),
    ("biofuels_energy_share_pct", "Biofuels", "#7cb518"),
    (
        "other_renewables_including_bioenergy_energy_share_pct",
        "Other renewables",
        "#5b8c5a",
    ),
]
# All band columns plus the reported low-carbon share (for the dark line)
g3_cols = [c for c, _, _ in g3_components] + ["low_carbon_energy_share_pct"]
g3 = prepare(cdf, g3_cols)

if len(g3) < 2:
    st.info("Not enough data for this chart (need at least 2 years).")
else:
    # The dark line is the reported low-carbon total; the bands should reach it
    stacked_area_chart(
        g3, g3_components, total_col="low_carbon_energy_share_pct", total_label="Reported low-carbon total"
    )
    # Explains how to read gaps or overshoots between the bands and the dark line
    st.caption(
        "Missing source values are counted as 0. If the bands don't reach the dark line, "
        "some low-carbon energy isn't broken out in the data; if they exceed it, "
        "'Other renewables' likely overlaps with biofuels."
    )

# Separator between the energy-mix charts and the decoupling chart
st.divider()


# Decoupling chart: GDP vs energy vs CO2 vs CO2 per capita, indexed to start = 100

st.subheader(f"{country}: Growth vs. Energy vs. Emissions (Index, start = 100)")

# Keep only years where every series is available so the lines share one baseline
ddf = cdf[["year", "gdp_ppp", "total_energy_twh", "co2", "co2_per_capita"]].dropna()

# Need at least two years to draw lines
if len(ddf) < 2:
    st.info("Not enough data for the decoupling chart.")
else:
    # First available year of the selection; every series is divided by its value here
    base = ddf.iloc[0]
    # Lines to draw: (column, legend label, color)
    series = [
        ("gdp_ppp", "GDP (PPP)", "#549e01"),
        ("total_energy_twh", "Energy use", "#ffb413"),
        ("co2", "CO₂ emissions", "#ff4935"),
        ("co2_per_capita", "Per capita emissions", "#AB0A0A"),
    ]

    # New figure and axes for this chart
    fig2, ax2 = plt.subplots(figsize=(11, 4.5), dpi=130)
    # Will track the highest indexed value, to size the y-axis
    ymax = 0
    # Draw one line (and its soft fill) per series
    for col, label, color in series:
        # Index = value / first-year value x 100, so every line starts at 100
        y = (ddf[col] / base[col] * 100).to_numpy()
        # Years for the horizontal axis
        x2 = ddf["year"].to_numpy()
        # Light colored area between the line and zero
        ax2.fill_between(x2, y, 0, color=color, alpha=0.15, linewidth=0)
        # The line itself, with its legend label
        ax2.plot(x2, y, label=label, color=color, linewidth=2)
        # Keep the largest value seen so far
        ymax = max(ymax, y.max())

    # Dashed gray line at 100 = the starting level, for easy comparison
    ax2.axhline(100, color="#888888", linewidth=0.8, linestyle="--")
    # Horizontal axis spans exactly the available years
    ax2.set_xlim(ddf["year"].min(), ddf["year"].max())
    # Vertical axis from 0 (so the fills have a baseline) to the highest value plus 8% headroom
    ax2.set_ylim(0, ymax * 1.08)
    # Y-axis title shows which year equals 100
    ax2.set_ylabel(f"Index ({int(base['year'])} = 100)", fontsize=9, color="#444444")
    # Whole-year ticks on the x-axis
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
    # Light horizontal grid, drawn behind the data
    ax2.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax2.set_axisbelow(True)
    # Hide the top and right frame lines
    ax2.spines[["top", "right"]].set_visible(False)
    # Tick label size and color
    ax2.tick_params(labelsize=9, colors="#444444")
    # Legend inside the plot, without a box
    ax2.legend(frameon=False, fontsize=9)

    # Fit everything in the figure, show it in Streamlit, then free the memory
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)