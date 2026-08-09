from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PLN_BLUE = "#0077C8"
PLN_DARK = "#103A5D"
PLN_YELLOW = "#F9C642"
GREEN = "#16A36A"
AMBER = "#F59E0B"
RED = "#D64545"
LIGHT_BLUE = "#DFF3FC"
GREY = "#667085"


def pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "–"
    return f"{value * 100:.1f}%".replace(".", ",")


def number(value: float | int) -> str:
    return f"{int(value):,}".replace(",", ".")


def chart_layout(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color=PLN_DARK),
        legend_title_text="",
    )
    return fig


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def get_ctx() -> dict:
    """Data dan agregat yang dihitung sekali di app.py, dipakai lintas halaman."""
    return st.session_state["dashboard_ctx"]
