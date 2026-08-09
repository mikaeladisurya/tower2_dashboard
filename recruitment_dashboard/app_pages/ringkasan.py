from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_common import AMBER, GREEN, PLN_DARK, PLN_BLUE, RED, chart_layout, get_ctx, hero, number, pct

ctx = get_ctx()
scoped_apps = ctx["scoped_apps"]
funnel = ctx["funnel"]
stage_summary = ctx["stage_summary"]
vacancy_summary = ctx["vacancy_summary"]
region_summary = ctx["region_summary"]

hero(
    "Recruitment Intelligence Dashboard",
    "Ringkasan end-to-end rekrutmen, fulfilment kebutuhan, dan perhatian utama untuk HCTA.",
)

kpis = st.columns(6)
kpis[0].metric("Total Pendaftar", number(ctx["applicants"]))
kpis[1].metric("Aktif dalam Proses", number(ctx["active"]))
kpis[2].metric("Lolos Wawancara", number(ctx["interview_passed"]))
kpis[3].metric("Kontrak Ditandatangani", number(ctx["signed"]))
kpis[4].metric("Pendaftar → Kontrak", pct(ctx["applicant_to_contract"]))
kpis[5].metric("Placement Alignment", pct(ctx["alignment"]))

left, right = st.columns([1.75, 1])
with left:
    fig = go.Figure(
        go.Funnel(
            y=funnel["STAGE"],
            x=funnel["COUNT"],
            textinfo="value+percent initial",
            marker={"color": [PLN_DARK, PLN_BLUE, "#1594D0", "#35A7D8", AMBER, "#6E9EC0", GREEN]},
            connector={"line": {"color": "#CDD7E1"}},
        )
    )
    fig.update_layout(title="Funnel Rekrutmen")
    st.plotly_chart(chart_layout(fig, 440), width="stretch")

with right:
    st.markdown("### Insight Utama")
    bottleneck = stage_summary.sort_values(["SLA Compliance", "Median Hari"]).iloc[0]
    critical = vacancy_summary[vacancy_summary["VACANCY_PRIORITY"].eq("CRITICAL")]
    critical_fill = critical["SIGNED"].sum() / critical["QUOTA"].sum() if len(critical) else np.nan
    remote_signed = scoped_apps[
        scoped_apps["INTERVIEW_RESULT"].eq("LOLOS") & scoped_apps["REMOTE_FLAG"].eq(1)
    ]
    nonremote_signed = scoped_apps[
        scoped_apps["INTERVIEW_RESULT"].eq("LOLOS") & scoped_apps["REMOTE_FLAG"].eq(0)
    ]
    remote_rate = remote_signed["CONTRACT_STATUS"].eq("SIGNED").mean() if len(remote_signed) else np.nan
    nonremote_rate = nonremote_signed["CONTRACT_STATUS"].eq("SIGNED").mean() if len(nonremote_signed) else np.nan
    st.markdown(
        f'<div class="insight"><b>Bottleneck utama: {bottleneck["Tahap"]}</b><br>'
        f'Median {bottleneck["Median Hari"]:.1f} hari vs SLA {bottleneck["Target SLA"]:.0f} hari.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="insight"><b>Fulfilment vacancy kritis: {pct(critical_fill)}</b><br>'
        "Masih tertinggal dibanding vacancy normal.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="insight"><b>Konversi kontrak remote: {pct(remote_rate)}</b><br>'
        f'Non-remote mencapai {pct(nonremote_rate)}.</div>',
        unsafe_allow_html=True,
    )

col1, col2 = st.columns([1.35, 1])
with col1:
    region_long = region_summary.melt(
        id_vars="REGION", value_vars=["QUOTA", "SIGNED"], var_name="Metric", value_name="Jumlah"
    )
    region_long["Metric"] = region_long["Metric"].map({"QUOTA": "Kuota", "SIGNED": "Kontrak"})
    fig = px.bar(
        region_long,
        y="REGION",
        x="Jumlah",
        color="Metric",
        barmode="group",
        orientation="h",
        color_discrete_map={"Kuota": "#B8C7D4", "Kontrak": PLN_BLUE},
        title="Kuota vs Kontrak per Wilayah",
    )
    st.plotly_chart(chart_layout(fig), width="stretch")
with col2:
    contract_counts = scoped_apps["CONTRACT_STATUS"].value_counts().rename_axis("Status").reset_index(name="Jumlah")
    fig = px.bar(
        contract_counts,
        x="Status",
        y="Jumlah",
        color="Status",
        color_discrete_map={"SIGNED": GREEN, "PENDING": AMBER, "REJECTED": RED, "NOT_OFFERED": "#B8C7D4"},
        title="Status Kontrak",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(chart_layout(fig), width="stretch")

st.markdown("### Vacancy yang Memerlukan Perhatian")
attention = vacancy_summary.sort_values(["VACANCY_PRIORITY", "FILL_RATE"], ascending=[True, True]).head(12).copy()
attention["Fulfilment"] = attention["FILL_RATE"].map(pct)
st.dataframe(
    attention[
        ["VACANCY_ID", "POSITION_NAME", "UNIT_NAME", "LOCATION_PLAN", "VACANCY_PRIORITY", "QUOTA", "SIGNED", "GAP", "Fulfilment"]
    ],
    width="stretch",
    hide_index=True,
)
