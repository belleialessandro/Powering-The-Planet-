"""Statistical tests and scenario modeling using NumPy, Pandas, and SciPy."""

import numpy as np
import pandas as pd
from scipy import stats


def gdp_co2_correlation(df: pd.DataFrame, year: int) -> dict[str, float | int]:
    """Compute Spearman rank and log-linear Pearson correlations between GDP/capita and CO2/capita."""
    sub = df[
        (df["year"] == year)
        & (~df["iso_code"].str.startswith("OWID_", na=True))
    ][["gdp_pc_ppp", "co2_per_capita"]].dropna()

    # Require at least 3 paired observations for correlation statistics
    if len(sub) < 3:
        return {"n": len(sub), "spearman_r": np.nan, "spearman_p": np.nan, "pearson_r": np.nan}

    sp = stats.spearmanr(sub["gdp_pc_ppp"], sub["co2_per_capita"])
    # Log10 transform GDP/capita to match the log-scaled Kuznets relationship
    pe = stats.pearsonr(np.log10(sub["gdp_pc_ppp"]), sub["co2_per_capita"])
    return {
        "n": len(sub),
        "spearman_r": float(sp.statistic),
        "spearman_p": float(sp.pvalue),
        "pearson_r": float(pe.statistic),
    }


def simulate_transition(row: pd.Series, coal_cut_pct: float, gas_cut_pct: float) -> dict[str, float]:
    """Estimate CO2 savings (Mt) from replacing a share of coal and gas with zero-carbon energy."""
    total_twh = float(row["total_energy_twh"])
    co2_mt = float(row["co2"])

    coal_twh = total_twh * float(row.get("coal_energy_share_pct", 0.0) or 0.0) / 100.0
    oil_twh = total_twh * float(row.get("oil_energy_share_pct", 0.0) or 0.0) / 100.0
    gas_twh = total_twh * float(row.get("gas_energy_share_pct", 0.0) or 0.0) / 100.0

    # Relative fuel emission weights calibrated to the country's reported CO2 emissions
    raw_est = 0.34 * coal_twh + 0.26 * oil_twh + 0.20 * gas_twh
    scale = (co2_mt / raw_est) if raw_est > 0 else 1.0

    saved_coal = (coal_twh * (coal_cut_pct / 100.0)) * 0.34 * scale
    saved_gas = (gas_twh * (gas_cut_pct / 100.0)) * 0.20 * scale
    total_saved = saved_coal + saved_gas

    return {
        "baseline_co2_mt": co2_mt,
        "saved_co2_mt": total_saved,
        "new_co2_mt": max(0.0, co2_mt - total_saved),
        "reduction_pct": (total_saved / co2_mt * 100.0) if co2_mt > 0 else 0.0,
    }