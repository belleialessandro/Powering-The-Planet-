import os
import pandas as pd

RAW_DIR = "data/raw"
OUT_PATH = "data/dataset.csv"
START_YEAR = 1960

# =====================================================================
# SELECT THE COLUMNS YOU WANT TO KEEP FROM EACH DATASET
# ("iso_code" and "year" are always kept automatically as merge keys)
# =====================================================================
SELECTED_ENERGY_COLS = [
    "country",
    "iso_code",
    "population",
    "year",
    "solar_energy_share_pct",
    "wind_energy_share_pct",
    "nuclear_energy_share_pct",
    "oil_energy_share_pct",
    "gas_energy_share_pct",
    "coal_energy_share_pct",
    "total_energy_twh",
]

SELECTED_CO2_COLS = [
    "co2",
    "co2_per_capita",
    "share_global_co2",
]

# World Bank GDP indicators (set to False if you don't want one of them)
KEEP_WB_GDP_PC = True     # -> column "gdp_pc_ppp"
KEEP_WB_GDP_TOTAL = True  # -> column "gdp_ppp"
# =====================================================================


def load_owid_catalog(filename, keep_cols):
    df = pd.read_csv(os.path.join(RAW_DIR, filename))
    df = df[df["iso_code"].notna() & (df["year"] >= START_YEAR)]
    cols = ["iso_code", "year"] + [c for c in keep_cols if c not in ("iso_code", "year")]
    return df[cols]


def load_owid_grapher(filename, target_col_name):
    df = pd.read_csv(os.path.join(RAW_DIR, filename))
    df = df[df["code"].notna() & (df["year"] >= START_YEAR)]
    val_col = [c for c in df.columns if c not in ("entity", "code", "year")][0]
    return df.rename(columns={"code": "iso_code", val_col: target_col_name})[
        ["iso_code", "year", target_col_name]
    ]


if __name__ == "__main__":
    keys = ["iso_code", "year"]

    energy = load_owid_catalog("owid_energy.csv", SELECTED_ENERGY_COLS)
    co2 = load_owid_catalog("owid_co2.csv", SELECTED_CO2_COLS)

    # Drop any CO2 column already selected in ENERGY_COLS to prevent _x / _y suffixes
    co2 = co2[keys + [c for c in co2.columns if c not in energy.columns]]

    df = energy.merge(co2, on=keys, how="left")

    if KEEP_WB_GDP_PC:
        gdp_pc = load_owid_grapher("wb_gdp_pc.csv", "gdp_pc_ppp")
        df = df.merge(gdp_pc, on=keys, how="left")

    if KEEP_WB_GDP_TOTAL:
        gdp_total = load_owid_grapher("wb_gdp_total.csv", "gdp_ppp")
        df = df.merge(gdp_total, on=keys, how="left")

    df = df.sort_values(keys).reset_index(drop=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved polished dataset to {OUT_PATH} ({df.shape[0]} rows, {df.shape[1]} columns)")