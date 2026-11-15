from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker  # axis formatters / tick locators
import numpy as np
import pandas as pd
import streamlit as st

# Page setup: browser tab title/icon and a wide layout so charts use the full width
st.set_page_config(page_title="Powering the Planet", page_icon="🌍", layout="wide")

# Build the CSV path relative to this file, so the app runs from any working directory
DATA_PATH = Path(__file__).resolve().parent / "data" / "dataset.csv"

# Columns the energy-mix charts depend on; used below to validate the dataset
SELECTED_ENERGY_COLS = [
    "country",
    "iso_code",
    "population",
    "year",
    "solar_energy_share_pct",
    "wind_energy_share_pct",
    "hydro_energy_share_pct",
    "biofuels_energy_share_pct",
    "other_renewables_including_bioenergy_energy_share_pct",
    "nuclear_energy_share_pct",
    "oil_energy_share_pct",
    "gas_energy_share_pct",
    "coal_energy_share_pct",
    "fossil_fuels_energy_share_pct",
    "renewables_energy_share_pct",
    "low_carbon_energy_share_pct",
    "total_energy_twh",
]


# Data loading
@st.cache_data  # cached: the CSV is read once, not on every rerun
def load_data(path: Path) -> pd.DataFrame:
    # Sort by country and year so "last row" always means "latest year"
    return pd.read_csv(path).sort_values(["country", "year"]).reset_index(drop=True)


# Stop early with a clear message if the file is missing
if not DATA_PATH.exists():
    st.error(f"Dataset not found at `{DATA_PATH}`.")
    st.stop()

df = load_data(DATA_PATH)

# Stop early if any required energy column is missing from the CSV
missing_cols = [c for c in SELECTED_ENERGY_COLS if c not in df.columns]
if missing_cols:
    st.error(f"Missing columns in dataset: {missing_cols}")
    st.stop()

# -----------------------------------------------------------------------------
# Sidebar: country and year-range filters
# -----------------------------------------------------------------------------
countries = sorted(df["country"].dropna().unique())
default_idx = countries.index("Italy") if "Italy" in countries else 0  # Italy by default
country = st.sidebar.selectbox("Select Country", countries, index=default_idx)

# Keep only the selected country's rows
cdf = df[df["country"] == country].copy()

# Slider bounds come from that country's available years; default window = last 30 years
min_y, max_y = int(cdf["year"].min()), int(cdf["year"].max())
default_start = max(min_y, max_y - 30)
years = st.sidebar.slider("Year Range", min_y, max_y, (default_start, max_y))
cdf = cdf[cdf["year"].between(years[0], years[1])]  # apply the year filter


def latest_value(data: pd.DataFrame, col: str):
    """Return (value, year) of the most recent non-null entry in `col`."""
    valid = data[["year", col]].dropna()
    if valid.empty:
        return np.nan, None
    last_row = valid.iloc[-1]  # data is sorted by year, so the last row is the latest
    return last_row[col], int(last_row["year"])


# Header and KPI tiles (latest available value for each metric)
iso = cdf["iso_code"].iloc[0] if not cdf.empty else ""
st.title(f"🌍 {country} ({iso})")

co2_val, co2_yr = latest_value(cdf, "co2")
gdp_val, gdp_yr = latest_value(cdf, "gdp_ppp")
eng_val, eng_yr = latest_value(cdf, "total_energy_twh")

k1, k2, k3 = st.columns(3)
k1.metric(
    f"Total CO₂ ({co2_yr or 'N/A'})",
    f"{co2_val:,.1f} Mt" if not np.isnan(co2_val) else "N/A",
)
k2.metric(
    f"Total GDP, PPP ({gdp_yr or 'N/A'})",
    f"${gdp_val / 1e9:,.1f} B" if not np.isnan(gdp_val) else "N/A",  # shown in billions
)
k3.metric(
    f"Total Energy Consumed ({eng_yr or 'N/A'})",
    f"{eng_val:,.1f} TWh" if not np.isnan(eng_val) else "N/A",
)

st.divider()


# Helpers for the stacked time-series charts
def to_twh(data: pd.DataFrame, share_col: str) -> np.ndarray:
    """Convert a '% of total energy' column into TWh (missing values count as 0)."""
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
    x = data["year"].to_numpy()
    layers = [to_twh(data, c) for c, _, _ in components]  # one TWh series per source
    labels = [l for _, l, _ in components]
    colors = [col for _, _, col in components]

    fig, ax = plt.subplots(figsize=(11, height), dpi=130)

    # Stacked bands; linewidth=0 removes outlines for a smooth look
    ax.stackplot(x, layers, labels=labels, colors=colors, alpha=0.85, linewidth=0)

    top = np.sum(layers, axis=0)  # height of the stack, used to scale the y-axis
    if total_col is not None:
        if total_col == "total_energy_twh":
            total_line = data["total_energy_twh"].to_numpy()  # already in TWh
        else:
            total_line = to_twh(data, total_col)  # share column -> TWh
        # Dark line = reported total; it should sit on top of the stack if the parts add up
        ax.plot(x, total_line, color="#222222", linewidth=1.6, label=total_label)
        top = np.maximum(top, total_line)  # keep the line inside the y-range

    # Axis range and formatting
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0, top.max() * 1.05)  # 5% headroom
    ax.set_ylabel("Primary energy (TWh)", fontsize=9, color="#444444")
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))  # thousands separators
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))  # whole-year ticks
    ax.tick_params(labelsize=9, colors="#444444")

    # Light horizontal grid behind the data, minimal spines
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#888888")

    # Legend below the plot, one column per entry (+1 for the total line if present)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=len(labels) + (1 if total_col else 0),
        frameon=False,
        fontsize=9,
    )

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)  # free memory; Streamlit reruns create many figures


def prepare(data: pd.DataFrame, share_cols: list) -> pd.DataFrame:
    """Keep rows with a total and at least one non-null share."""
    out = data[["year", "total_energy_twh"] + share_cols].dropna(subset=["total_energy_twh"])
    return out.dropna(how="all", subset=share_cols).reset_index(drop=True)


# Graph 1: Total energy = Low carbon + Fossil fuels
st.subheader(f"{country}: Total Energy Consumption — Low Carbon vs. Fossil Fuels")

g1_components = [  # (column, legend label, color), bottom to top
    ("fossil_fuels_energy_share_pct", "Fossil fuels", "#6b4f4a"),
    ("low_carbon_energy_share_pct", "Low carbon", "#2a9d8f"),
]
g1 = prepare(cdf, [c for c, _, _ in g1_components])

if len(g1) < 2:  # an area chart needs at least two points
    st.info("Not enough data for this chart (need at least 2 years).")
else:
    # The dark line is total consumption; if the stack doesn't reach it,
    # part of the energy is classified as neither fossil nor low carbon
    stacked_area_chart(
        g1, g1_components, total_col="total_energy_twh", total_label="Total energy consumption"
    )
    st.caption(
        "Band thickness = TWh of primary energy. The dark line is total consumption; "
        "if the bands don't reach it, part of the energy isn't classified as fossil or low carbon."
    )


# Graph 2: Fossil fuels = Coal + Oil + Gas
st.subheader(f"{country}: Fossil Fuel Consumption by Source")

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
    stacked_area_chart(
        g2, g2_components, total_col="fossil_fuels_energy_share_pct", total_label="Reported fossil total"
    )

# Graph 3: Low carbon = Nuclear + Hydro + Wind + Solar + Biofuels + Other renewables
st.subheader(f"{country}: Low-Carbon Energy by Source")

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
g3_cols = [c for c, _, _ in g3_components] + ["low_carbon_energy_share_pct"]
g3 = prepare(cdf, g3_cols)

if len(g3) < 2:
    st.info("Not enough data for this chart (need at least 2 years).")
else:
    stacked_area_chart(
        g3, g3_components, total_col="low_carbon_energy_share_pct", total_label="Reported low-carbon total"
    )
    st.caption(
        "Missing source values are counted as 0. If the bands don't reach the dark line, "
        "some low-carbon energy isn't broken out in the data; if they exceed it, "
        "'Other renewables' likely overlaps with biofuels."
    )

st.divider()


# Decoupling chart: GDP vs energy vs CO2 vs CO2 per capita, indexed to start = 100
st.subheader(f"{country}: Growth vs. Energy vs. Emissions (Index, start = 100)")

# Keep only years where every series is available so the lines share one baseline
ddf = cdf[["year", "gdp_ppp", "total_energy_twh", "co2", "co2_per_capita"]].dropna()

if len(ddf) < 2:
    st.info("Not enough data for the decoupling chart.")
else:
    base = ddf.iloc[0]  # first year of the selection = 100
    series = [  # (column, legend label, color)
        ("gdp_ppp", "GDP (PPP)", "#549e01"),
        ("total_energy_twh", "Energy use", "#ffb413"),
        ("co2", "CO₂ emissions", "#ff4935"),
        ("co2_per_capita", "Per capita emissions", "#AB0A0A"),
    ]

    fig2, ax2 = plt.subplots(figsize=(11, 4.5), dpi=130)
    ymax = 0
    for col, label, color in series:
        y = (ddf[col] / base[col] * 100).to_numpy()  # rescale so the first year = 100
        x2 = ddf["year"].to_numpy()
        ax2.fill_between(x2, y, 0, color=color, alpha=0.15, linewidth=0)  # soft fill under the line
        ax2.plot(x2, y, label=label, color=color, linewidth=2)
        ymax = max(ymax, y.max())  # track the highest value for the y-limit

    ax2.axhline(100, color="#888888", linewidth=0.8, linestyle="--")  # baseline reference
    ax2.set_xlim(ddf["year"].min(), ddf["year"].max())
    ax2.set_ylim(0, ymax * 1.08)  # start at 0 so the fills have a baseline
    ax2.set_ylabel(f"Index ({int(base['year'])} = 100)", fontsize=9, color="#444444")
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
    ax2.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax2.set_axisbelow(True)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.tick_params(labelsize=9, colors="#444444")
    ax2.legend(frameon=False, fontsize=9)

    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)