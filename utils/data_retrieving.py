import os
import requests
import wbgapi as wb
import pandas as pd

# Direct URL to the OWID Energy CSV (latest energy dataset)
OWID_ENERGY_URL = "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv"
OWID_ENERGY_PATH = os.path.join("data", "owid_energy.csv")

# d Direct URL to the OWID CO2 CSV (latest co2 dataset)
OWID_CO2_URL = "https://catalog.ourworldindata.org/emissions/owid_co2/owid_co2.csv"
OWID_CO2_PATH = os.path.join("data", "owid_co2.csv")

# World Bank: GDP per capita, PPP, constant international $
WB_INDICATOR = "NY.GDP.PCAP.PP.KD"
WB_PATH = os.path.join("data", "wb_gdp_pc_ppp.csv")


# Download function 
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

def download_wb(indicator, path, start=1970, end=2023):
    """Fetch a World Bank indicator with wbgapi and save it as a long CSV
    (iso_code, year, gdp_pc_ppp), unless it is already on disk."""
    if os.path.exists(path):
        return
    wide = wb.data.DataFrame(
        indicator,
        time=range(start, end + 1),
        labels=False,
        skipAggs=True,  # drop regional aggregates (World, Euro area, ...)
    )
    long = wide.reset_index().melt(
        id_vars="economy", var_name="year", value_name="gdp_pc_ppp"
    )
    long["year"] = long["year"].str.replace("YR", "").astype(int)
    long = long.rename(columns={"economy": "iso_code"}).dropna()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    long.to_csv(path, index=False)

# My Data
download_file(OWID_ENERGY_URL, OWID_ENERGY_PATH)
download_file(OWID_CO2_URL, OWID_CO2_PATH)
download_wb(WB_INDICATOR, WB_PATH)



