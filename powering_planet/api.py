"""Download OWID and World Bank data and build the merged dataset."""

import os
import pandas as pd
import requests

RAW_DIR = os.path.join("data", "raw")
OUT_PATH = os.path.join("data", "dataset.csv")
START_YEAR = 1960

URLS = {
    "owid_energy.csv": "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv",
    "owid_co2.csv": "https://catalog.ourworldindata.org/emissions/owid_co2/owid_co2.csv",
    "wb_gdp_pc.csv": "https://ourworldindata.org/grapher/gdp-per-capita-worldbank.csv?v=1&csvType=full&useColumnShortNames=true",
    "wb_gdp_total.csv": "https://ourworldindata.org/grapher/gdp-worldbank.csv?v=1&csvType=full&useColumnShortNames=true",
}

ENERGY_COLS = [
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

CO2_COLS = ["iso_code", "year", "co2", "co2_per_capita", "share_global_co2"]


def download_file(url, path):
    """Download a file from the web if it is not already on disk."""
    if os.path.exists(path):
        return
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)


def download_all(raw_dir=RAW_DIR):
    """Download all raw CSV files."""
    for filename, url in URLS.items():
        path = os.path.join(raw_dir, filename)
        download_file(url, path)


def load_catalog_csv(path, cols, start_year=START_YEAR):
    """Load an OWID catalog CSV and filter by year and ISO code."""
    df = pd.read_csv(path)
    df = df[df["iso_code"].notna() & (df["year"] >= start_year)]
    return df[cols].copy()


def load_grapher_csv(path, new_col, start_year=START_YEAR):
    """Load an OWID grapher CSV and rename its value column."""
    df = pd.read_csv(path)
    df = df[df["code"].notna() & (df["year"] >= start_year)]

    value_col = None
    for col in df.columns:
        if col not in ("entity", "code", "year"):
            value_col = col
            break

    df = df.rename(columns={"code": "iso_code", value_col: new_col})
    return df[["iso_code", "year", new_col]].copy()


def build_dataset(raw_dir=RAW_DIR, out_path=OUT_PATH, start_year=START_YEAR):
    """Merge energy, CO2, and GDP tables and save to CSV."""
    energy = load_catalog_csv(os.path.join(raw_dir, "owid_energy.csv"), ENERGY_COLS, start_year)
    co2 = load_catalog_csv(os.path.join(raw_dir, "owid_co2.csv"), CO2_COLS, start_year)
    gdp_pc = load_grapher_csv(os.path.join(raw_dir, "wb_gdp_pc.csv"), "gdp_pc_ppp", start_year)
    gdp_total = load_grapher_csv(os.path.join(raw_dir, "wb_gdp_total.csv"), "gdp_ppp", start_year)

    df = energy.merge(co2, on=["iso_code", "year"], how="left")
    df = df.merge(gdp_pc, on=["iso_code", "year"], how="left")
    df = df.merge(gdp_total, on=["iso_code", "year"], how="left")
    df = df.sort_values(["iso_code", "year"]).reset_index(drop=True)

    folder = os.path.dirname(out_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    download_all()
    build_dataset()