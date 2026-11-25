# 🌍 Powering the Planet

An interactive Python data science package and multi-page **Streamlit** web application for exploring global primary energy mixes, economic growth vs. CO₂ emissions decoupling, head-to-head country comparisons, and counterfactual decarbonization scenarios.

Built for the **Coding for Data Science and Data Management** course (M.Sc. in Data Science for Economics and Health, Università degli Studi di Milano).

---

## ✨ Key Features

- **Country Energy Profiles & Decarbonization Simulator (`pages/country_profile.py`)**
  - Interactive time-series breakdown of primary energy consumption (low-carbon vs. fossil fuels, and disaggregated fuel shares across coal, oil, gas, nuclear, hydro, wind, solar, biofuels, and other renewables).
  - Automated **GDP–Energy–CO₂ decoupling classification** (*Absolute Decoupling*, *Relative Decoupling*, or *Coupled Growth*) computed via Compound Annual Growth Rates (CAGR), plus an indexed trajectory comparison chart.
  - Interactive **What-If Fossil Phase-Out Simulator** estimating CO₂ reductions (Mt) from replacing shares of **coal, oil, and natural gas** with zero-carbon energy, alongside a full country-level data table.
- **Head-to-Head Country Comparison (`pages/compare.py`)**
  - Side-by-side comparison of any two countries across key energy, emissions, and macroeconomic metrics over a shared year range.
  - Direct trajectory overlay charts and parallel primary energy mix breakdowns.
- **Global Energy Transition Ranking (`pages/ranking.py`)**
  - **Core Transition Ranking:** Cross-country leaderboard with a 1st–3rd podium and full table ranked by low-carbon energy share, renewables share, lowest carbon intensity (Mt CO₂ / TWh), or lowest energy intensity (TWh / $B GDP), with one-click CSV export.
  - **Top 10 Countries by Feature:** Interactive horizontal bar chart ranking the top 10 countries for any selected energy, emissions, or economic indicator.
- **Modular Python Backend (`powering_planet/`)**
  - Object-oriented package (`EnergyDataset`, `CountryProfile`) separating automated data ingestion, preprocessing, scenario modeling, and Plotly visualizations from the Streamlit UI.

---

## 📊 Data Sources

The automated pipeline (`powering_planet/api.py`) fetches and merges four open macroeconomic and energy datasets from 1960 onward:
1. **Our World in Data (OWID) — Energy Data:** Primary energy consumption (TWh), population, and energy mix shares by source.
2. **Our World in Data (OWID) — CO₂ and Greenhouse Gas Emissions:** Annual territorial CO₂ emissions (Mt), CO₂ per capita, and share of global CO₂.
3. **World Bank Open Data (via OWID Grapher):** GDP per capita, PPP (constant international $).
4. **World Bank Open Data (via OWID Grapher):** Total GDP, PPP (constant international $).

---

## 🚀 Quickstart: Running Locally on Another Machine

### 1. Clone the repository
```bash
git clone https://github.com/belleialessandro/Powering-The-Planet-.git
cd Powering-The-Planet-
```

### 2. Create and activate a virtual environment
**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download and build the dataset
Run the data pipeline to fetch the raw OWID and World Bank CSVs into `data/raw/` and generate the merged panel dataset at `data/dataset.csv`:
```bash
python -m powering_planet.api
```

### 5. Launch the Streamlit app
```bash
streamlit run app.py
```
Open the local URL printed in the terminal (typically `http://localhost:8501`).

---

## 🗂️ Project Structure

```text
Powering-The-Planet-/
├── app.py                   # Streamlit multi-page application entrypoint
├── pyproject.toml           # Package build configuration
├── requirements.txt         # Project dependencies
├── data/
│   ├── raw/                 # Cached raw source CSVs (downloaded via api.py)
│   └── dataset.csv          # Cleaned, merged panel dataset
├── notebooks/
│   ├── inspect.ipynb        # Pre-merge CSV exploration
│   └── walkthrough.ipynb    # Demonstration and visual walkthrough
├── pages/
│   ├── country_profile.py   # Country energy mix, decoupling, simulator & data table
│   ├── compare.py           # Head-to-head country comparison page
│   └── ranking.py           # Global transition leaderboard, Top 10 chart & CSV export
└── powering_planet/
    ├── __init__.py
    ├── api.py               # Automated data fetching and preprocessing pipeline
    ├── dataset.py           # EnergyDataset and CountryProfile classes
    ├── metrics.py           # Energy groups, intensity metrics, CAGR & flag helpers
    ├── analysis.py          # Scenario modeling for fossil fuel phase-out
    └── plots.py             # Interactive Plotly charts
```