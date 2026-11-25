"""Statistical tests and scenario modeling using NumPy, Pandas, and SciPy."""

import numpy as np
import pandas as pd
from scipy import stats


def gdp_co2_correlation(df: pd.DataFrame, year: int) -> dict[str, float | int]:
    """Compute Spearman rank and log-linear Pearson correlations between GDP/capita and CO2/capita."""
    # Keep only non-aggregate rows for the selected year that have both GDP/capita and CO2/capita
    sub = df[
        (df["year"] == year)
        & (~df["iso_code"].str.startswith("OWID_", na=True))
    ][["gdp_pc_ppp", "co2_per_capita"]].dropna()

    # Need at least 3 countries to calculate meaningful correlation statistics
    if len(sub) < 3:
        return {"n": len(sub), "spearman_r": np.nan, "spearman_p": np.nan, "pearson_r": np.nan}

    # Spearman checks whether richer countries also tend to rank higher in per-capita emissions
    sp = stats.spearmanr(sub["gdp_pc_ppp"], sub["co2_per_capita"])

    # Take log10 of GDP/capita first so the relationship looks closer to a straight line (Kuznets curve)
    pe = stats.pearsonr(np.log10(sub["gdp_pc_ppp"]), sub["co2_per_capita"])

    return {
        "n": len(sub),
        "spearman_r": float(sp.statistic),
        "spearman_p": float(sp.pvalue),
        "pearson_r": float(pe.statistic),
    }


def simulate_transition(
    row: pd.Series,
    coal_cut_pct: float,
    oil_cut_pct: float = 0.0,
    gas_cut_pct: float = 0.0,
) -> dict[str, float]:
    """Estimate CO2 savings (Mt) from replacing shares of coal, oil, and gas with zero-carbon energy."""
    total_twh = float(row["total_energy_twh"])
    co2_mt = float(row["co2"])

    # Convert each fossil fuel's percentage share into energy volume (TWh), defaulting to 0 if missing
    coal_twh = total_twh * float(row.get("coal_energy_share_pct", 0.0) or 0.0) / 100.0
    oil_twh = total_twh * float(row.get("oil_energy_share_pct", 0.0) or 0.0) / 100.0
    gas_twh = total_twh * float(row.get("gas_energy_share_pct", 0.0) or 0.0) / 100.0

    # Relative emission weights (coal > oil > gas), scaled so the raw estimate matches reported CO2
    raw_est = 0.34 * coal_twh + 0.26 * oil_twh + 0.20 * gas_twh
    scale = (co2_mt / raw_est) if raw_est > 0 else 1.0

    # Calculate CO2 saved (Mt) for each fuel based on the chosen % cut
    saved_coal = (coal_twh * (coal_cut_pct / 100.0)) * 0.34 * scale
    saved_oil = (oil_twh * (oil_cut_pct / 100.0)) * 0.26 * scale
    saved_gas = (gas_twh * (gas_cut_pct / 100.0)) * 0.20 * scale
    total_saved = saved_coal + saved_oil + saved_gas

    return {
        "baseline_co2_mt": co2_mt,
        "saved_co2_mt": total_saved,
        "new_co2_mt": max(0.0, co2_mt - total_saved),
        "reduction_pct": (total_saved / co2_mt * 100.0) if co2_mt > 0 else 0.0,
    }