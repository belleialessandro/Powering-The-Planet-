"""Constants and simple helper functions for energy and growth metrics."""

import numpy as np
import pandas as pd

# Lists 
OVERVIEW_SOURCES = [
    ("fossil_fuels_energy_share_pct", "Fossil fuels"),
    ("low_carbon_energy_share_pct", "Low carbon"),
]

FOSSIL_SOURCES = [
    ("coal_energy_share_pct", "Coal"),
    ("oil_energy_share_pct", "Oil"),
    ("gas_energy_share_pct", "Gas"),
]

LOW_CARBON_SOURCES = [
    ("nuclear_energy_share_pct", "Nuclear"),
    ("hydro_energy_share_pct", "Hydro"),
    ("wind_energy_share_pct", "Wind"),
    ("solar_energy_share_pct", "Solar"),
    ("biofuels_energy_share_pct", "Biofuels"),
    ("other_renewables_including_bioenergy_energy_share_pct", "Other renewables"),
]

# Dictionaries
COLORS = {
    "Fossil fuels": "#6d597a",
    "Low carbon": "#2a9d8f",
    "Coal": "#4a4a4a",
    "Oil": "#c65d6e",
    "Gas": "#83589c",
    "Nuclear": "#2b6cb0",
    "Hydro": "#1d78b5",
    "Wind": "#2a9d8f",
    "Solar": "#e9c46a",
    "Biofuels": "#7cb518",
    "Other renewables": "#5b8c5a",
}

METRIC_OPTIONS = {
    "Low-Carbon Energy Share (%)": ("low_carbon_energy_share_pct", False), # False/True = Descending/Ascending
    "Renewables Energy Share (%)": ("renewables_energy_share_pct", False),
    "Lowest Carbon Intensity (Mt/TWh)": ("carbon_intensity_energy", True),
    "Lowest Energy Intensity (TWh/$B GDP)": ("energy_intensity_gdp", True), 
}

FEATURE_OPTIONS = {
    "Total Energy (TWh)": "total_energy_twh", # "Label name": "Variable name"
    "Total CO2 (Mt)": "co2",
    "CO2 per Capita (t)": "co2_per_capita",
    "GDP per Capita PPP ($)": "gdp_pc_ppp",
    "GDP PPP ($)": "gdp_ppp",
    "Low-Carbon Energy Share (%)": "low_carbon_energy_share_pct",
    "Renewables Energy Share (%)": "renewables_energy_share_pct",
    "Solar Share (%)": "solar_energy_share_pct",
    "Wind Share (%)": "wind_energy_share_pct",
    "Hydro Share (%)": "hydro_energy_share_pct",
    "Nuclear Share (%)": "nuclear_energy_share_pct",
    "Coal Share (%)": "coal_energy_share_pct",
    "Gas Share (%)": "gas_energy_share_pct",
    "Oil Share (%)": "oil_energy_share_pct",
    "Population": "population",
}

# Useful metrics
def add_intensity_columns(df):
    """Add carbon intensity (Mt/TWh) and energy intensity (TWh/$B GDP)."""
    out = df.copy()
    energy_safe = out["total_energy_twh"].replace(0, np.nan)
    gdp_billions = (out["gdp_ppp"] / 1e9).replace(0, np.nan)

    out["carbon_intensity_energy"] = out["co2"] / energy_safe
    out["energy_intensity_gdp"] = out["total_energy_twh"] / gdp_billions
    return out


def share_to_twh(df, share_col):
    """I dont have the actual value in TWh for each energy source --> i convert an energy share column into TWh"""
    share = df[share_col].fillna(0)
    return df["total_energy_twh"] * share / 100


def compute_cagr(start_val, end_val, years):
    """Computes Compound Annual Growth Rate in percent."""
    if years <= 0 or pd.isna(start_val) or pd.isna(end_val):
        return np.nan
    if start_val <= 0 or end_val <= 0:
        return np.nan
    return float(((end_val / start_val) ** (1 / years) - 1) * 100)
