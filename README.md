# 🌍 Powering the Planet

An interactive Python data science package and multi-page **Streamlit** web application for exploring global primary energy mixes, economic growth vs. CO₂ emissions decoupling, head-to-head country comparisons, and counterfactual decarbonization scenarios.

Built for the **Coding for Data Science and Data Management** course (M.Sc. in Data Science for Economics and Health, Università degli Studi di Milano).

---

## ✨ Key Features

- **Country Energy Profiles (`pages/country_profile.py`)**
  - Interactive time-series breakdown of primary energy consumption (low-carbon vs. fossil fuels, and disaggregated fuel shares across coal, oil, gas, nuclear, hydro, wind, solar, and biofuels).
  - Automated **GDP–Energy–CO₂ decoupling classification** (*Absolute Decoupling*, *Relative Decoupling*, or *Coupled Growth*) computed via Compound Annual Growth Rates (CAGR).
- **Head-to-Head Country Comparison (`pages/compare.py`)**
  - Side-by-side comparison of any two countries across key energy, emissions, and macroeconomic metrics over a shared year range.
  - Direct trajectory overlay charts and parallel primary energy mix breakdowns.
- **Global Energy Transition Ranking (`pages/ranking.py`)**
  - Filterable cross-country leaderboard ranked by low-carbon energy share, renewables share, carbon intensity (Mt CO₂ / TWh), or energy intensity (TWh / $B GDP), with one-click CSV export.
- **Cross-Country Insights & Decarbonization Simulator (`pages/insights.py`)**
  - Statistical correlation analysis (Spearman rank ρ and log-linear Pearson *r*) between GDP per capita (PPP) and CO₂ emissions per capita.
  - Interactive **What-If Fossil Phase-Out Simulator** estimating CO₂ reductions (Mt) from replacing coal and natural gas shares with zero-carbon energy.
- **Modular Python Backend (`powering_planet/`)**
  - Object-oriented package (`EnergyDataset`, `CountryProfile`) separating data ingestion, statistical modeling, and Plotly visualizations from the Streamlit UI.

---

## 📊 Data Sources

The pipeline integrates three open macroeconomic and energy datasets:
1. **Our World in Data (OWID) — Energy Data:** Primary energy consumption (TWh) and energy mix shares by source.
2. **Our World in Data (OWID) — CO₂ and Greenhouse Gas Emissions:** Annual territorial CO₂ emissions (Mt), CO₂ per capita, and population.
3. **World Bank Open Data (`NY.GDP.PCAP.PP.KD`):** GDP per capita, PPP (constant 2021 international $).

---

## 🗂️ Project Structure

```text
Powering-The-Planet-/
├── app.py                        # Streamlit multiple page application entrypoint
├── pyproject.toml                # Package build configuration
├── requirements.txt              # Python dependencies
├── data/
│   ├── raw/                      # Raw source files (excluded in .gitignore)
│   └── dataset.csv               # Cleaned, merged panel dataset
├── notebooks/
│   └── walkthrough.ipynb         # End-to-end demonstration of the Python API
├── pages/
│   ├── country_profile.py        # Country energy mix & decoupling page
│   ├── compare.py                # Head-2-head comparison page
│   ├── ranking.py                # Global leaderboard & CSV export page
│   └── insights.py               # GDP/CO2 scatter & transition simulator page
└── powering_planet/
    ├── __init__.py
    ├── api.py                    # Data fetching and preprocessing pipeline
    ├── dataset.py                # EnergyDataset and CountryProfile classes
    ├── metrics.py                # Energy groups, intensity metrics, CAGR & flag helpers
    ├── analysis.py               # Statistical correlation & counterfactual simulator
    └── plots.py                  # Interactive Plotly chart builders