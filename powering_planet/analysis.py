"""Scenario modeling for energy transition simulations."""

import pandas as pd


def simulate_transition(
    row: pd.Series,
    coal_cut_pct: float,
    oil_cut_pct: float = 0.0,
    gas_cut_pct: float = 0.0,
) -> dict[str, float]:
    """Estimate CO2 savings (Mt) from replacing shares of coal, oil, and gas with zero-carbon energy."""
    # Pull total energy (TWh) and total CO2 emissions (Mt) for the selected baseline year
    total_twh = float(row["total_energy_twh"])
    co2_mt = float(row["co2"])

    # Turn each fuel's share (%) into actual energy volume in TWh (treating missing shares as 0%)
    coal_twh = total_twh * float(row.get("coal_energy_share_pct", 0.0) or 0.0) / 100.0
    oil_twh = total_twh * float(row.get("oil_energy_share_pct", 0.0) or 0.0) / 100.0
    gas_twh = total_twh * float(row.get("gas_energy_share_pct", 0.0) or 0.0) / 100.0

    # Relative emission weights per TWh (coal > oil > gas), scaled to match the country's reported CO2
    raw_est = 0.34 * coal_twh + 0.26 * oil_twh + 0.20 * gas_twh
    scale = (co2_mt / raw_est) if raw_est > 0 else 1.0

    # Compute CO2 saved (Mt) for each cut slider percentage and sum them up
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