"""Simple scenario calculation for replacing fossil fuels with zero-carbon energy."""

import pandas as pd

def simulate_phase_out(row, coal_cut_pct, oil_cut_pct=0, gas_cut_pct=0):
    """Estimate CO2 savings (Mt) when cutting coal, oil, and gas shares."""
    total_twh = float(row["total_energy_twh"])
    co2_mt = float(row["co2"])

    coal_share = 0.0 if pd.isna(row.get("coal_energy_share_pct")) else float(row["coal_energy_share_pct"])
    oil_share = 0.0 if pd.isna(row.get("oil_energy_share_pct")) else float(row["oil_energy_share_pct"])
    gas_share = 0.0 if pd.isna(row.get("gas_energy_share_pct")) else float(row["gas_energy_share_pct"])

    coal_twh = total_twh * coal_share / 100
    oil_twh = total_twh * oil_share / 100
    gas_twh = total_twh * gas_share / 100

    # Relative emission factors (coal > oil > gas) scaled to match reported CO2
    raw_co2 = 0.34 * coal_twh + 0.26 * oil_twh + 0.20 * gas_twh
    scale = co2_mt / raw_co2 if raw_co2 > 0 else 1.0

    saved_coal = coal_twh * (coal_cut_pct / 100) * 0.34 * scale
    saved_oil = oil_twh * (oil_cut_pct / 100) * 0.26 * scale
    saved_gas = gas_twh * (gas_cut_pct / 100) * 0.20 * scale
    saved_total = saved_coal + saved_oil + saved_gas

    new_co2 = max(0.0, co2_mt - saved_total)
    reduction_pct = (saved_total / co2_mt * 100) if co2_mt > 0 else 0.0

    return {
        "baseline_co2_mt": co2_mt,
        "saved_co2_mt": saved_total,
        "new_co2_mt": new_co2,
        "reduction_pct": reduction_pct,
    }