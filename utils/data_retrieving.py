import pandas as pd
import streamlit as st
import os
import requests

# Direct URL to the OWID Energy CSV (new energy dataset)
OWID_ENERGY_URL = "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv"
OWID_ENERGY_PATH = os.path.join("data", "owid_energy.csv")


def download_file(url, path):
    """Download from the web, unless it is already on disk."""
    if os.path.exists(path):
        return
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(response.content)


download_file(OWID_ENERGY_URL, OWID_ENERGY_PATH)

