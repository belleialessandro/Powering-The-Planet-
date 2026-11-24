"""Reusable Plotly figure builders (free of Streamlit dependencies)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .metrics import share_to_twh


def plot_stacked_energy(
    df: pd.DataFrame,
    components: list[tuple[str, str, str]],
    total_col: str | None = None,
    total_label: str = "Reported total",
) -> go.Figure:
    """Build an interactive stacked area chart of primary energy consumption in TWh."""
    fig = go.Figure()

    for col, label, color in components:
        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=share_to_twh(df, col),
                name=label,
                mode="lines",
                stackgroup="one",
                line=dict(width=0.5, color=color),
                fillcolor=color,
                hovertemplate="%{y:,.1f} TWh<extra>" + label + "</extra>",
            )
        )

    if total_col is not None:
        y_total = df["total_energy_twh"] if total_col == "total_energy_twh" else share_to_twh(df, total_col)
        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=y_total,
                name=total_label,
                mode="lines",
                line=dict(color="#222222", width=2),
                hovertemplate="%{y:,.1f} TWh<extra>" + total_label + "</extra>",
            )
        )

    fig.update_layout(
        hovermode="x unified",
        yaxis_title="Primary energy (TWh)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=20, b=60),
        height=400,
    )
    return fig


def plot_decoupling_index(df: pd.DataFrame) -> go.Figure:
    """Build an indexed (start year = 100) line chart comparing GDP, energy, and CO2."""
    ddf = df[["year", "gdp_ppp", "total_energy_twh", "co2", "co2_per_capita"]].dropna()
    base = ddf.iloc[0]
    base_year = int(base["year"])

    series = [
        ("gdp_ppp", "GDP (PPP)", "#549e01"),
        ("total_energy_twh", "Energy use", "#ffb413"),
        ("co2", "CO₂ emissions", "#ff4935"),
        ("co2_per_capita", "Per capita emissions", "#ab0a0a"),
    ]

    fig = go.Figure()
    for col, label, color in series:
        fig.add_trace(
            go.Scatter(
                x=ddf["year"],
                y=ddf[col] / base[col] * 100.0,
                name=label,
                mode="lines",
                line=dict(color=color, width=2.5),
                hovertemplate="%{y:,.1f}<extra>" + label + "</extra>",
            )
        )

    fig.add_hline(y=100, line_dash="dash", line_color="#888888", line_width=1)
    fig.update_layout(
        hovermode="x unified",
        yaxis_title=f"Index ({base_year} = 100)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=20, b=60),
        height=400,
    )
    return fig


def plot_kuznets_scatter(df: pd.DataFrame, year: int) -> go.Figure:
    """Build a bubble scatter plot of GDP per capita vs. CO2 per capita colored by low-carbon share."""
    sub = df[
        (df["year"] == year)
        & (~df["iso_code"].str.startswith("OWID_", na=True))
    ].dropna(subset=["gdp_pc_ppp", "co2_per_capita", "population"])

    fig = px.scatter(
        sub,
        x="gdp_pc_ppp",
        y="co2_per_capita",
        size="population",
        color="low_carbon_energy_share_pct",
        hover_name="country",
        log_x=True,
        color_continuous_scale="Tealgrn",
        labels={
            "gdp_pc_ppp": "GDP per capita, PPP ($, log scale)",
            "co2_per_capita": "CO₂ per capita (tonnes)",
            "low_carbon_energy_share_pct": "Low-Carbon Share (%)",
        },
        height=480,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return fig