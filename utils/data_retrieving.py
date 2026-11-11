import os
import requests
import wbgapi as wb
import pandas as pd

# Project root = parent of the utils/ folder, so paths work from anywhere
# (terminal, notebook, Streamlit) no matter the current working directory.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Direct URL to the OWID Energy CSV (latest energy dataset)
OWID_ENERGY_URL = "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv"
OWID_ENERGY_PATH = os.path.join(DATA_DIR, "owid_energy.csv")

# Direct URL to the OWID CO2 CSV (latest co2 dataset)
OWID_CO2_URL = "https://catalog.ourworldindata.org/emissions/owid_co2/owid_co2.csv"
OWID_CO2_PATH = os.path.join(DATA_DIR, "owid_co2.csv")

# World Bank: GDP Per Capita on Purchansing Power Parity ($)
WB_INDICATOR = "NY.GDP.PCAP.PP.KD"
WB_PATH = os.path.join(DATA_DIR, "wb_gdp_pc_ppp.csv")


# Download functions
def download_file(url, path):
    """Download from the web, unless it is already on disk. If server does not respond
    then timeout of 30s and raise error if status/client problem"""
    if os.path.exists(path):
        return
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(response.content)


def download_wb(indicator, path, start=1990, end=2026):
    """Fetch a World Bank indicator with wbgapi and save it as a long CSV
    (iso_code, year, gdp_pc_ppp), unless it is already on disk."""
    if os.path.exists(path):
        return
    wide = wb.data.DataFrame(
        indicator,
        time=range(start, end + 1),
        labels=False,
        skipAggs=True,  # drop regional aggregates labels
    )
    long = wide.reset_index().melt(
        id_vars="economy", var_name="year", value_name="gdp_pc_ppp"
    )
    long["year"] = long["year"].str.replace("YR", "").astype(int)
    long = long.rename(columns={"economy": "iso_code"}).dropna()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    long.to_csv(path, index=False)


# My Data >= 1990
def trim_file(path, starting_year=1990):
    """Keep only rows from starting_year onwards and overwrite the file."""
    df = pd.read_csv(path)
    df[df["year"] >= starting_year].to_csv(path, index=False)


def fetch_all():
    """Download every dataset the project needs (if files already downloaded skip)."""
    for url, path in ((OWID_ENERGY_URL, OWID_ENERGY_PATH), (OWID_CO2_URL, OWID_CO2_PATH)):
        is_new = not os.path.exists(path)
        download_file(url, path)
        if is_new:
            trim_file(path)  # only trim files that were just downloaded
    download_wb(WB_INDICATOR, WB_PATH)  # already starts at START_YEAR


if __name__ == "__main__":  # python utils/data_retrieving.py still downloads everything
    fetch_all()


