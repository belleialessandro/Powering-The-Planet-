"""Domain entity representing a single country's energy, emissions, and GDP trajectory."""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from .metrics import compute_cagr


@dataclass
class CountryProfile:
    country: str
    iso_code: str
    df: pd.DataFrame

    def latest(self, col: str) -> tuple[float, int | None]:
        """Return (value, year) for the most recent non-null observation in `col`."""
        valid = self.df[["year", col]].dropna()
        if valid.empty:
            return np.nan, None
        # Assumes self.df is sorted chronologically by year
        row = valid.iloc[-1]
        return float(row[col]), int(row["year"])

    def decoupling_summary(self) -> dict[str, float | str]:
        """Classify GDP vs. CO2 growth rates across the profile's time window."""
        valid = self.df[["year", "gdp_ppp", "co2"]].dropna()
        if len(valid) < 2:
            return {"status": "Insufficient data", "gdp_cagr": np.nan, "co2_cagr": np.nan}

        first, last = valid.iloc[0], valid.iloc[-1]
        span = int(last["year"] - first["year"])
        gdp_cagr = compute_cagr(first["gdp_ppp"], last["gdp_ppp"], span)
        co2_cagr = compute_cagr(first["co2"], last["co2"], span)

        # Absolute: GDP rises while CO2 falls; Relative: GDP rises faster than CO2
        if gdp_cagr > 0 and co2_cagr < 0:
            status = "Absolute Decoupling"
        elif gdp_cagr > 0 and co2_cagr < gdp_cagr:
            status = "Relative Decoupling"
        else:
            status = "Coupled / No Growth"

        return {"status": status, "gdp_cagr": gdp_cagr, "co2_cagr": co2_cagr}