"""Constants and simple helper functions for energy and growth metrics."""

import numpy as np
import pandas as pd

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

def fmt_diff(val_1, val_2, fmt, suffix=""):
    """Format val_1 - val_2 with a sign, or None if either value is missing."""
    if np.isnan(val_1) or np.isnan(val_2):
        return None
    return f"{val_1 - val_2:{fmt}}{suffix}"