"""Dataset loader, validator, and query interface."""

from pathlib import Path
import pandas as pd
from .metrics import add_derived_metrics
from .models import CountryProfile

REQUIRED_ENERGY_COLS = [
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


class EnergyDataset:
    """Encapsulates the merged global energy, emissions, and GDP dataset."""

    def __init__(self, df: pd.DataFrame):
        missing = [c for c in REQUIRED_ENERGY_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        self.df = add_derived_metrics(df).sort_values(["country", "year"]).reset_index(drop=True)

    @classmethod
    def load(cls, path: str | Path = "data/dataset.csv") -> "EnergyDataset":
        return cls(pd.read_csv(path))

    def countries(self, include_aggregates: bool = False) -> list[str]:
        sub = self.df if include_aggregates else self.df[~self.df["iso_code"].str.startswith("OWID_", na=True)]
        return sorted(sub["country"].dropna().unique())

    def available_years(self) -> list[int]:
        return sorted(self.df["year"].dropna().astype(int).unique())

    def get_country(self, country: str, year_range: tuple[int, int] | None = None) -> CountryProfile:
        cdf = self.df[self.df["country"] == country].copy()
        if year_range is not None:
            cdf = cdf[cdf["year"].between(year_range[0], year_range[1])]
        iso = str(cdf["iso_code"].iloc[0]) if not cdf.empty else ""
        return CountryProfile(country=country, iso_code=iso, df=cdf)

    def ranking(
        self,
        year: int,
        sort_by: str = "low_carbon_energy_share_pct",
        ascending: bool = False,
        min_population: float = 1_000_000,
    ) -> pd.DataFrame:
        """Rank sovereign nations for a given year and population floor."""
        sub = self.df[
            (self.df["year"] == year)
            & (~self.df["iso_code"].str.startswith("OWID_", na=True))
            & (self.df["population"].fillna(0) >= min_population)
        ].copy()

        sub = sub.dropna(subset=[sort_by]).sort_values(sort_by, ascending=ascending).reset_index(drop=True)
        sub.insert(0, "rank", sub.index + 1)
        return sub