"""Simple Plotly chart functions (no Streamlit code here)."""

import pandas as pd
import plotly.express as px
from powering_planet.metrics import COLORS, share_to_twh

# Chart makers
def make_energy_chart(df, sources, title):
    """Build a stacked area chart of energy by type (TWh) over time."""
    plot_df = df[["year"]].copy()
    value_cols = []
    for col, label in sources:
        plot_df[label] = share_to_twh(df, col)
        value_cols.append(label)

    long_df = plot_df.melt(
        id_vars="year",
        value_vars=value_cols,
        var_name="Source",
        value_name="TWh",
    )
    fig = px.area(
        long_df,
        x="year",
        y="TWh",
        color="Source",
        color_discrete_map=COLORS,
        title=title,
        labels={"year": "Year", "TWh": "Primary Energy (TWh)"},
        template="plotly_white",
    )
    return fig


def make_decoupling_chart(df):
    """Build an indexed line chart (first year = 100) for GDP, energy, and CO2."""
    cols = ["year", "gdp_ppp", "total_energy_twh", "co2"]
    sub = df[cols].dropna().copy()
    if len(sub) < 2:
        return None

    base = sub.iloc[0]
    sub["GDP (PPP)"] = sub["gdp_ppp"] / base["gdp_ppp"] * 100
    sub["Energy Use"] = sub["total_energy_twh"] / base["total_energy_twh"] * 100
    sub["CO2 Emissions"] = sub["co2"] / base["co2"] * 100

    long_df = sub.melt(
        id_vars="year",
        value_vars=["GDP (PPP)", "Energy Use", "CO2 Emissions"],
        var_name="Indicator",
        value_name="Index",
    )
    base_year = int(base["year"])
    fig = px.line(
        long_df,
        x="year",
        y="Index",
        color="Indicator",
        color_discrete_map=COLORS,
        title=f"Indexed Trends ({base_year} = 100)",
        labels={"year": "Year", "Index": f"Index ({base_year} = 100)"},
        template="plotly_white",
    )
    return fig


def make_top10_bar(top_df, col, label, year):
    """Build a horizontal bar chart colored by value for the top 10 countries."""
    fig = px.bar(
        top_df,
        x=col,
        y="country",
        orientation="h",
        color=col,
        color_continuous_scale="Tealgrn",
        title=f"Top 10 Countries: {label} ({year})",
        labels={col: label, "country": "Country"},
        template="plotly_white",
    )
    fig.update_layout(yaxis={"autorange": "reversed"}, coloraxis_showscale=False)
    return fig


def make_energy_pie(df, sources, title, height=260):
    """Build a compact pie chart of energy mix (TWh) using the latest row in df."""
    if df.empty:
        return None

    last_df = df.tail(1)
    year = int(last_df["year"].iloc[0])

    rows = []
    for col, label in sources:
        val = float(share_to_twh(last_df, col).iloc[0])
        if val > 0:
            rows.append({"Source": label, "TWh": val})

    if not rows:
        return None

    pie_df = pd.DataFrame(rows)
    fig = px.pie(
        pie_df,
        names="Source",
        values="TWh",
        color="Source",
        color_discrete_map=COLORS,
        title=f"{title} ({year})",
        template="plotly_white",
        height=height,
    )
    fig.update_layout(margin=dict(t=40, b=10, l=10, r=10))
    return fig

def make_feature_scatter(sub_df, x_col, x_label, y_col, y_label, z_col, z_label, year):
    """Build a scatter plot comparing three features across countries for one year."""
    plot_df = sub_df.dropna(subset=[x_col, y_col]).copy()
    if plot_df.empty:
        return None

    size_col = "population" if "population" in plot_df.columns else None
    fig = px.scatter(
        plot_df,
        x=x_col,
        y=y_col,
        size=size_col,
        hover_name="country",
        color=z_col,
        color_continuous_scale="Tealgrn",
        title=f"{y_label} vs. {x_label} colouring by {z_label} ({year})",
        labels={x_col: x_label, y_col: y_label, "low_carbon_energy_share_pct": "Low-Carbon (%)"},
        template="plotly_white",
    )
    return fig
