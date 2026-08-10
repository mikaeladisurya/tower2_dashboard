from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_common import AMBER, GREEN, PLN_BLUE, RED, chart_layout, get_ctx, hero, number, pct
from data_layer import method_stage_matrix

ctx = get_ctx()
scoped_pipeline = ctx["scoped_pipeline"]
method_summary = ctx["method_summary"]
stage_summary = ctx["stage_summary"]
all_pipeline = ctx["all_pipeline"]
ids = ctx["ids"]

hero(
    "Pipeline & Recruitment Method",
    "Monitor performa setiap tahap, kepatuhan SLA, dan efektivitas metode rekrutmen.",
)

cols = st.columns(5)
cols[0].metric("Pipeline Events", number(len(scoped_pipeline)))
cols[1].metric("Aktif", number(ctx["active"]))
cols[2].metric("Event Over SLA", number(scoped_pipeline["SLA_STATUS"].eq("OVER_SLA").sum()))
cols[3].metric("Median End-to-End", f"{scoped_pipeline.groupby('ID_PENDAFTARAN')['DURATION_DAYS'].sum().median():.1f} hari")
cols[4].metric("Metode Aktif", number(method_summary["Metode"].nunique()))

left, right = st.columns([1.25, 1])
with left:
    stage_plot = stage_summary.copy()
    fig = go.Figure()
    fig.add_bar(name="Median Aktual", x=stage_plot["Tahap"], y=stage_plot["Median Hari"], marker_color=PLN_BLUE)
    fig.add_scatter(
        name="Target SLA",
        x=stage_plot["Tahap"],
        y=stage_plot["Target SLA"],
        mode="lines+markers",
        line=dict(color=RED, width=3),
    )
    fig.update_layout(title="Durasi Tahap vs Target SLA", barmode="group")
    st.plotly_chart(chart_layout(fig), width="stretch")
with right:
    compliance = stage_summary.copy()
    compliance["Compliance"] = compliance["SLA Compliance"] * 100
    fig = px.bar(
        compliance,
        x="Compliance",
        y="Tahap",
        orientation="h",
        color="Compliance",
        color_continuous_scale=[RED, AMBER, GREEN],
        range_color=[0, 100],
        title="SLA Compliance per Tahap",
    )
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(chart_layout(fig), width="stretch")

st.markdown("### Detail Performa Tahap")
stage_display = stage_summary.drop(columns="STAGE_CODE").copy()
stage_display["Pass Rate"] = stage_display["Pass Rate"].map(pct)
stage_display["SLA Compliance"] = stage_display["SLA Compliance"].map(pct)
stage_display["Median Hari"] = stage_display["Median Hari"].round(1)
stage_display["P90 Hari"] = stage_display["P90 Hari"].round(1)
st.dataframe(stage_display, width="stretch", hide_index=True)

st.markdown("### Perbandingan Metode Rekrutmen")
method_display = method_summary.copy().sort_values("Conversion", ascending=False)
method_display["Conversion"] = method_display["Conversion"].map(pct)
method_display["Placement Alignment"] = method_display["Placement Alignment"].map(pct)
method_display["Median Total Hari"] = method_display["Median Total Hari"].round(1)
st.dataframe(method_display, width="stretch", hide_index=True)

metric = st.selectbox("Metric heatmap", ["SLA Compliance", "Median Hari", "Pass Rate"])
matrix = method_stage_matrix(all_pipeline, ids, metric)
z = matrix.values * 100 if metric in {"SLA Compliance", "Pass Rate"} else matrix.values
suffix = "%" if metric in {"SLA Compliance", "Pass Rate"} else " hari"
fig = go.Figure(
    data=go.Heatmap(
        z=z,
        x=matrix.columns,
        y=matrix.index,
        colorscale="Blues" if metric != "Median Hari" else "YlOrRd",
        text=np.round(z, 1),
        texttemplate=f"%{{text}}{suffix}",
        hovertemplate="%{y}<br>%{x}<br>%{z:.1f}" + suffix + "<extra></extra>",
    )
)
fig.update_layout(title=f"{metric}: Metode × Tahap")
st.plotly_chart(chart_layout(fig, 410), width="stretch")

active_rows = scoped_pipeline[scoped_pipeline["STAGE_STATUS"].eq("IN_PROGRESS")].copy()
if len(active_rows):
    st.markdown("### Kandidat Aktif yang Memerlukan Monitoring")
    active_rows["OVERDUE_DAYS"] = (active_rows["DURATION_DAYS"] - active_rows["SLA_TARGET_DAYS"]).clip(lower=0).round(1)
    st.dataframe(
        active_rows.sort_values("OVERDUE_DAYS", ascending=False)[
            ["ID_PENDAFTARAN", "RECRUITMENT_METHOD", "STAGE_CODE", "DURATION_DAYS", "SLA_TARGET_DAYS", "SLA_STATUS", "OVERDUE_DAYS", "VACANCY_ID"]
        ].head(100),
        width="stretch",
        hide_index=True,
    )
