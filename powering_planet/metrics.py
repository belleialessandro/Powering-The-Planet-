"""Domain constants, energy source groupings, and intensity/growth formulas."""

import numpy as np
import pandas as pd

ENERGY_GROUPS: dict[str, list[tuple[str, str, str]]] = {
    "overview": [
        ("fossil_fuels_energy_share_pct", "Fossil fuels", "#6b4f4a"),
        ("low_carbon_energy_share_pct", "Low carbon", "#2a9d8f"),
    ],
    "fossil": [
        ("coal_energy_share_pct", "Coal", "#4a4a4a"),
        ("oil_energy_share_pct", "Oil", "#c65d6e"),
        ("gas_energy_share_pct", "Gas", "#83589c"),
    ],
    "low_carbon": [
        ("nuclear_energy_share_pct", "Nuclear", "#238b7e"),
        ("hydro_energy_share_pct", "Hydro", "#1d78b5"),
        ("wind_energy_share_pct", "Wind", "#1d3557"),
        ("solar_energy_share_pct", "Solar", "#f2a541"),
        ("biofuels_energy_share_pct", "Biofuels", "#7cb518"),
        ("other_renewables_including_bioenergy_energy_share_pct", "Other renewables", "#5b8c5a"),
    ],
}


def share_to_twh(df: pd.DataFrame, share_col: str) -> pd.Series:
    """Convert a percentage share column into primary energy (TWh)."""
    return df["total_energy_twh"] * df[share_col].fillna(0.0) / 100.0


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute carbon intensity of energy (Mt/TWh) and energy intensity of GDP (TWh/$B)."""
    out = df.copy()
    out["carbon_intensity_energy"] = out["co2"] / out["total_energy_twh"].replace(0, np.nan)
    gdp_billions = out["gdp_ppp"] / 1e9
    out["energy_intensity_gdp"] = out["total_energy_twh"] / gdp_billions.replace(0, np.nan)
    return out


def compute_cagr(start_val: float, end_val: float, years: int) -> float:
    """Compute Compound Annual Growth Rate (%)."""
    if years <= 0 or pd.isna(start_val) or pd.isna(end_val) or start_val <= 0 or end_val <= 0:
        return np.nan
    return float(((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0)