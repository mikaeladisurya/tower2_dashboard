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


def is_dark_theme() -> bool:
    return (st.context.theme.type or "light") == "dark"


def get_palette(is_dark: bool | None = None) -> dict[str, str]:
    """Theme-aware UI colors, mirroring .streamlit/config.toml's light/dark values where
    they're meant to line up. config.toml can't be read back at runtime (st.context.theme
    only exposes .type, not the resolved colors), so these are kept in sync by hand - card/
    popover tones are intentionally a bit different from config.toml's for visual elevation,
    that's not drift to "fix"."""
    if is_dark is None:
        is_dark = is_dark_theme()
    if is_dark:
        return {
            "card_bg": "#132C42",
            "card_border": "#1E3A52",
            "card_shadow": "rgba(0, 0, 0, 0.35)",
            "heading": "#EAF4FF",
            "badge_bg": "#173A57",
            "badge_text": "#BFE3FF",
            "popover_bg": "#24272C",
            "popover_border": "#3A3F46",
            # Borrowed from config.toml's dark textColor - chart backgrounds are transparent,
            # so this needs to read against the app's dark page background, not PLN_DARK.
            "chart_text": "#E7EEF5",
        }
    return {
        "card_bg": "#FFFFFF",
        "card_border": "#E7ECF2",
        "card_shadow": "rgba(16, 58, 93, 0.05)",
        "heading": PLN_DARK,
        "badge_bg": LIGHT_BLUE,
        "badge_text": PLN_DARK,
        "popover_bg": "#FFFFFF",
        "popover_border": "#E7ECF2",
        "chart_text": PLN_DARK,
    }


def chart_layout(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color=get_palette()["chart_text"]),
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
