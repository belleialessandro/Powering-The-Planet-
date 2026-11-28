"""Functions to load, filter, and rank country energy data."""

import os
import numpy as np
import pandas as pd
from powering_planet import metrics as m

DEFAULT_DATA_PATH = os.path.join("data", "dataset.csv")


def load_data(path=DEFAULT_DATA_PATH):
    """Load the merged CSV and add intensity columns."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at {path}. Run python -m powering_planet.api first.")
    df = pd.read_csv(path)
    df = m.add_intensity_columns(df)
    return df.sort_values(["country", "year"]).reset_index(drop=True)


def get_countries(df):
    """Return a sorted list of country names."""
    is_agg = df["iso_code"].fillna("").str.startswith("OWID_")
    sub = df[~is_agg]
    names = sub["country"].dropna().unique().tolist()
    return sorted(names)


def filter_country(df, country, years=None):
    """Return rows for one country, optionally filtered to a (start_year, end_year) tuple."""
    sub = df[df["country"] == country].copy()
    if years is not None:
        start_y, end_y = years
        sub = sub[(sub["year"] >= start_y) & (sub["year"] <= end_y)]
    return sub.sort_values("year").reset_index(drop=True)


def latest_value(df, col):
    """Return (value, year) for the latest non-missing value in a column."""
    valid = df[["year", col]].dropna()
    if valid.empty:
        return np.nan, None
    last_row = valid.iloc[-1]
    return float(last_row[col]), int(last_row["year"])


def decoupling_status(df):
    """Classify GDP vs. CO2 growth over a country DataFrame."""
    valid = df[["year", "gdp_ppp", "co2"]].dropna()
    if len(valid) < 2:
        return {"status": "Insufficient data", "gdp_cagr": np.nan, "co2_cagr": np.nan}

    first_row = valid.iloc[0]
    last_row = valid.iloc[-1]
    span = int(last_row["year"] - first_row["year"])

    gdp_cagr = m.compute_cagr(first_row["gdp_ppp"], last_row["gdp_ppp"], span)
    co2_cagr = m.compute_cagr(first_row["co2"], last_row["co2"], span)

    if pd.isna(gdp_cagr) or pd.isna(co2_cagr):
        status = "Insufficient data"
    elif gdp_cagr > 0 and co2_cagr < 0:
        status = "Absolute Decoupling"
    elif gdp_cagr > 0 and co2_cagr < gdp_cagr:
        status = "Relative Decoupling"
    else:
        status = "Coupled / No Growth"

    return {"status": status, "gdp_cagr": gdp_cagr, "co2_cagr": co2_cagr}


def rank_countries(df, year, sort_by, ascending=False):
    """Rank countries for a single year by a chosen column."""
    is_agg = df["iso_code"].fillna("").str.startswith("OWID_")
    sub = df[(df["year"] == year) & (~is_agg)].copy()
    sub = sub.dropna(subset=[sort_by])
    sub = sub.sort_values(sort_by, ascending=ascending).reset_index(drop=True)
    sub.insert(0, "rank", sub.index + 1)
    return sub