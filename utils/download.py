import os
import requests

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

DATASETS = {
    "owid_energy.csv": "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv",
    "owid_co2.csv": "https://catalog.ourworldindata.org/emissions/owid_co2/owid_co2.csv",
    "wb_gdp_pc.csv": "https://ourworldindata.org/grapher/gdp-per-capita-worldbank.csv?v=1&csvType=full&useColumnShortNames=true",
    "wb_gdp_total.csv": "https://ourworldindata.org/grapher/gdp-worldbank.csv?v=1&csvType=full&useColumnShortNames=true",
}


def download(url, path):
    if os.path.exists(path):
        print(f"Already exists: {path}")
        return
    print(f"Downloading {path}...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"Saved: {path}")


if __name__ == "__main__":
    for filename, url in DATASETS.items():
        download(url, os.path.join(RAW_DIR, filename))