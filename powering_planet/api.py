"""Data retrieval and preprocessing pipeline for OWID Energy, CO2, and World Bank GDP."""

from pathlib import Path
import pandas as pd
import requests

# Default directories and time cutoff for the cleaned panel dataset
RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/dataset.csv")
START_YEAR = 1960

# Local cache filenames mapped to OWID catalog and grapher download URLs
DATASETS = {
    "owid_energy.csv": "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv",
    "owid_co2.csv": "https://catalog.ourworldindata.org/emissions/owid_co2/owid_co2.csv",
    "wb_gdp_pc.csv": "https://ourworldindata.org/grapher/gdp-per-capita-worldbank.csv?v=1&csvType=full&useColumnShortNames=true",
    "wb_gdp_total.csv": "https://ourworldindata.org/grapher/gdp-worldbank.csv?v=1&csvType=full&useColumnShortNames=true",
}

# Core identifiers, total energy, and fuel share columns retained from OWID Energy
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

# Emissions metrics kept from OWID CO2 (keys/population come from energy table)
SELECTED_CO2_COLS = [
    "co2",
    "co2_per_capita",
    "share_global_co2",
]


def download_file(url: str, path: Path, force: bool = False) -> Path:
    """Download a single CSV file if not already cached locally."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Skip network download when cached unless force=True is requested
    if path.exists() and not force:
        return path
    response = requests.get(url, timeout=30)
    response.raise_for_status()  # Fail early on HTTP errors instead of saving error HTML
    path.write_bytes(response.content)
    return path


def download_all(raw_dir: Path = RAW_DIR, force: bool = False) -> None:
    """Fetch all raw OWID and World Bank datasets."""
    for filename, url in DATASETS.items():
        download_file(url, raw_dir / filename, force=force)


def _load_owid_catalog(path: Path, keep_cols: list[str], start_year: int) -> pd.DataFrame:
    """Load an OWID catalog CSV, drop rows without ISO codes, and filter years."""
    df = pd.read_csv(path)
    df = df[df["iso_code"].notna() & (df["year"] >= start_year)]
    # Always place merge keys first without duplicating them
    cols = ["iso_code", "year"] + [c for c in keep_cols if c not in ("iso_code", "year")]
    return df[cols]


def _load_owid_grapher(path: Path, target_col: str, start_year: int) -> pd.DataFrame:
    """Load an OWID grapher indicator CSV and standardize key and value column names."""
    df = pd.read_csv(path)
    df = df[df["code"].notna() & (df["year"] >= start_year)]
    # Identify the indicator column by excluding standard OWID metadata columns
    val_col = [c for c in df.columns if c not in ("entity", "code", "year")][0]
    return df.rename(columns={"code": "iso_code", val_col: target_col})[["iso_code", "year", target_col]]


def build_dataset(raw_dir: Path = RAW_DIR, out_path: Path = OUT_PATH, start_year: int = START_YEAR) -> pd.DataFrame:
    """Merge raw energy, CO2, and GDP tables on (iso_code, year) and save to CSV."""
    keys = ["iso_code", "year"]

    # Load energy as base table and left-join CO2 without duplicating overlapping columns
    energy = _load_owid_catalog(raw_dir / "owid_energy.csv", SELECTED_ENERGY_COLS, start_year)
    co2 = _load_owid_catalog(raw_dir / "owid_co2.csv", SELECTED_CO2_COLS, start_year)
    co2 = co2[keys + [c for c in co2.columns if c not in energy.columns]]

    df = energy.merge(co2, on=keys, how="left")

    # Left-join World Bank PPP GDP per capita and total GDP so energy rows are preserved
    gdp_pc = _load_owid_grapher(raw_dir / "wb_gdp_pc.csv", "gdp_pc_ppp", start_year)
    df = df.merge(gdp_pc, on=keys, how="left")

    gdp_total = _load_owid_grapher(raw_dir / "wb_gdp_total.csv", "gdp_ppp", start_year)
    df = df.merge(gdp_total, on=keys, how="left")

    # Sort deterministically and write clean CSV without DataFrame index column
    df = df.sort_values(keys).reset_index(drop=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df

# Runs only when i execute python -m powering_planet.api or python powering_planet/api.py directly from terminal
if __name__ == "__main__":
    download_all()
    build_dataset()

    