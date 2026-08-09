from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_common import GREEN, PLN_BLUE, PLN_YELLOW, RED, chart_layout, get_ctx, hero, number, pct

ctx = get_ctx()
scoped_apps = ctx["scoped_apps"]
region_summary = ctx["region_summary"]
placements = ctx["placements"]

hero(
    "Sebaran Rekrutmen & Penempatan",
    "Bandingkan kebutuhan, hasil kontrak, dan kesesuaian penempatan akhir terhadap rencana.",
)

cols = st.columns(4)
cols[0].metric("Total Kuota", number(ctx["quota"]))
cols[1].metric("Kontrak", number(ctx["signed"]))
cols[2].metric("Quota Fulfilment", pct(ctx["quota_fulfilment"]))
cols[3].metric("Exact Alignment", pct(ctx["alignment"]))

left, right = st.columns([1.4, 1])
with left:
    region_long = region_summary.melt(
        id_vars="REGION", value_vars=["QUOTA", "SIGNED", "GAP"], var_name="Metric", value_name="Jumlah"
    )
    region_long["Metric"] = region_long["Metric"].map({"QUOTA": "Kuota", "SIGNED": "Kontrak", "GAP": "Gap"})
    fig = px.bar(
        region_long,
        x="REGION",
        y="Jumlah",
        color="Metric",
        barmode="group",
        color_discrete_map={"Kuota": "#B8C7D4", "Kontrak": PLN_BLUE, "Gap": RED},
        title="Sebaran Kebutuhan dan Pemenuhan",
    )
    st.plotly_chart(chart_layout(fig), width="stretch")
with right:
    alignment_counts = placements["ALIGNMENT_CATEGORY"].value_counts().rename_axis("Kategori").reset_index(name="Jumlah")
    fig = px.pie(
        alignment_counts,
        values="Jumlah",
        names="Kategori",
        hole=0.62,
        color="Kategori",
        color_discrete_map={"Fully Aligned": GREEN, "Partially Aligned": PLN_YELLOW, "Not Aligned": RED},
        title="Kesesuaian Penempatan",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(chart_layout(fig), width="stretch")

left, right = st.columns([1, 1.4])
with left:
    rejection = (
        scoped_apps.loc[scoped_apps["CONTRACT_STATUS"].eq("REJECTED"), "CONTRACT_REJECTION_REASON"]
        .value_counts()
        .rename_axis("Alasan")
        .reset_index(name="Jumlah")
    )
    fig = px.bar(
        rejection,
        y="Alasan",
        x="Jumlah",
        orientation="h",
        color="Jumlah",
        color_continuous_scale="YlOrRd",
        title="Alasan Penolakan Kontrak",
    )
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(chart_layout(fig), width="stretch")
with right:
    matrix = pd.crosstab(placements["REGION_PLAN"], placements["REGION_ACTUAL"])
    fig = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale="Blues",
            text=matrix.values,
            texttemplate="%{text}",
        )
    )
    fig.update_layout(title="Perpindahan Wilayah: Rencana → Aktual")
    st.plotly_chart(chart_layout(fig), width="stretch")

region_table = region_summary.copy()
region_table["Fulfilment"] = region_table["FILL_RATE"].map(pct)
st.dataframe(region_table[["REGION", "QUOTA", "SIGNED", "GAP", "Fulfilment"]], width="stretch", hide_index=True)
