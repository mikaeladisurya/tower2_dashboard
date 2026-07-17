from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chatbot import answer_question, build_chat_context, llm_is_configured
from data_layer import (
    STAGE_LABELS,
    STAGE_ORDER,
    build_funnel,
    load_demo_data,
    method_performance,
    method_stage_matrix,
    placement_detail,
    region_fulfilment,
    score_candidates_for_vacancy,
    selected_application_ids,
    stage_performance,
    vacancy_fulfilment,
)


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"

PLN_BLUE = "#0077C8"
PLN_DARK = "#103A5D"
PLN_YELLOW = "#F9C642"
GREEN = "#16A36A"
AMBER = "#F59E0B"
RED = "#D64545"
LIGHT_BLUE = "#DFF3FC"
GREY = "#667085"


st.set_page_config(
    page_title="PLN Recruitment Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: #F5F8FB; }}
      [data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid #E5EAF0; }}
      .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
      h1, h2, h3 {{ color: {PLN_DARK}; }}
      [data-testid="stMetric"] {{
        background: white;
        border: 1px solid #E7ECF2;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 3px 12px rgba(16, 58, 93, 0.05);
      }}
      .hero {{
        background: linear-gradient(110deg, {PLN_DARK}, {PLN_BLUE});
        color: white;
        border-radius: 18px;
        padding: 22px 26px;
        margin-bottom: 18px;
      }}
      .hero h1 {{ color: white; margin: 0; font-size: 1.8rem; }}
      .hero p {{ margin: 6px 0 0 0; opacity: .88; }}
      .insight {{
        background: white;
        border-left: 5px solid {PLN_YELLOW};
        border-radius: 10px;
        padding: 13px 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 10px rgba(16, 58, 93, 0.05);
      }}
      .demo-badge {{
        display: inline-block;
        background: {LIGHT_BLUE};
        color: {PLN_DARK};
        padding: 5px 10px;
        border-radius: 999px;
        font-size: .78rem;
        font-weight: 700;
      }}
      .small-note {{ color: {GREY}; font-size: .83rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Memuat data demo...")
def get_data() -> dict[str, pd.DataFrame]:
    return load_demo_data(DATA_DIR)


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


data = get_data()
apps = data["applications"]
vacancies = data["vacancies"]
pipeline = data["pipeline"]


with st.sidebar:
    st.markdown("## ⚡ PLN Recruitment")
    st.markdown('<span class="demo-badge">SYNTHETIC DEMO DATA</span>', unsafe_allow_html=True)
    st.write("")
    page = st.radio(
        "Navigasi",
        [
            "Ringkasan",
            "Pipeline & Metode",
            "Sebaran & Penempatan",
            "Kecocokan Kandidat",
        ],
        label_visibility="collapsed",
    )

    st.markdown("### Filter")
    programs = st.multiselect(
        "Program Rekrutmen",
        sorted(apps["NAMA REKRUTMEN"].dropna().unique()),
        placeholder="Semua program",
    )
    regions = st.multiselect(
        "Wilayah Rencana",
        sorted(apps["REGION_PLAN"].dropna().unique()),
        placeholder="Semua wilayah",
    )
    methods = st.multiselect(
        "Metode Rekrutmen",
        sorted(apps["RECRUITMENT_METHOD"].dropna().unique()),
        placeholder="Semua metode",
    )

ids = selected_application_ids(apps, programs, regions, methods)
if not ids:
    st.warning("Tidak ada data yang sesuai dengan kombinasi filter yang dipilih.")
    st.stop()
scoped_apps = apps[apps["ID_PENDAFTARAN"].isin(ids)].copy()
scoped_pipeline = pipeline[pipeline["ID_PENDAFTARAN"].isin(ids)].copy()
funnel = build_funnel(pipeline, ids)
stage_summary = stage_performance(pipeline, ids)
method_summary = method_performance(apps, pipeline, ids)
vacancy_summary = vacancy_fulfilment(vacancies, apps, ids, programs, regions)
region_summary = region_fulfilment(vacancy_summary)
placements = placement_detail(apps, ids)

applicants = len(scoped_apps)
interview_passed = int(scoped_apps["INTERVIEW_RESULT"].eq("LOLOS").sum())
signed = int(scoped_apps["CONTRACT_STATUS"].eq("SIGNED").sum())
active = int(scoped_pipeline["STAGE_STATUS"].eq("IN_PROGRESS").sum())
applicant_to_contract = signed / applicants if applicants else 0
quota = int(vacancy_summary["QUOTA"].sum())
quota_fulfilment = int(vacancy_summary["SIGNED"].sum()) / quota if quota else 0
alignment = placements["EXACT_PLACEMENT_MATCH"].mean() if len(placements) else 0

overview_context = {
    "applicants": applicants,
    "interview_passed": interview_passed,
    "signed": signed,
    "active": active,
    "applicant_to_contract": applicant_to_contract,
    "quota_fulfilment": quota_fulfilment,
    "placement_alignment": alignment,
    "filters": {"programs": programs, "regions": regions, "methods": methods},
}
chat_context = build_chat_context(
    overview_context,
    stage_summary,
    method_summary,
    region_summary,
    vacancy_summary,
)


with st.sidebar:
    st.divider()
    with st.expander("💬 Recruitment Copilot", expanded=False):
        status = "LLM aktif" if llm_is_configured() else "Mode demo tanpa API"
        st.caption(status)
        suggestions = [
            "Berapa persen pendaftar sampai kontrak?",
            "Tahap mana yang menjadi bottleneck?",
            "Metode mana yang paling efektif?",
            "Vacancy kritis mana yang belum terpenuhi?",
        ]
        selected_suggestion = st.selectbox(
            "Pertanyaan contoh",
            ["Tulis pertanyaan sendiri..."] + suggestions,
            label_visibility="collapsed",
        )
        typed_question = st.text_area(
            "Pertanyaan",
            value="" if selected_suggestion.startswith("Tulis") else selected_suggestion,
            height=90,
            placeholder="Tanyakan funnel, SLA, metode, penempatan...",
        )
        if st.button("Tanyakan", type="primary", use_container_width=True):
            if typed_question.strip():
                response = answer_question(typed_question, chat_context)
                st.session_state.setdefault("chat_history", []).append((typed_question, response))
        for question, response in st.session_state.get("chat_history", [])[-2:]:
            st.markdown(f"**Anda:** {question}")
            st.markdown(response)


if page == "Ringkasan":
    hero(
        "Recruitment Intelligence Dashboard",
        "Ringkasan end-to-end rekrutmen, fulfilment kebutuhan, dan perhatian utama untuk HCTA.",
    )

    kpis = st.columns(6)
    kpis[0].metric("Total Pendaftar", number(applicants))
    kpis[1].metric("Aktif dalam Proses", number(active))
    kpis[2].metric("Lolos Wawancara", number(interview_passed))
    kpis[3].metric("Kontrak Ditandatangani", number(signed))
    kpis[4].metric("Pendaftar → Kontrak", pct(applicant_to_contract))
    kpis[5].metric("Placement Alignment", pct(alignment))

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
        use_container_width=True,
        hide_index=True,
    )


elif page == "Pipeline & Metode":
    hero(
        "Pipeline & Recruitment Method",
        "Monitor performa setiap tahap, kepatuhan SLA, dan efektivitas metode rekrutmen.",
    )

    cols = st.columns(5)
    cols[0].metric("Pipeline Events", number(len(scoped_pipeline)))
    cols[1].metric("Aktif", number(active))
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
    st.dataframe(stage_display, use_container_width=True, hide_index=True)

    st.markdown("### Perbandingan Metode Rekrutmen")
    method_display = method_summary.copy().sort_values("Conversion", ascending=False)
    method_display["Conversion"] = method_display["Conversion"].map(pct)
    method_display["Placement Alignment"] = method_display["Placement Alignment"].map(pct)
    method_display["Median Total Hari"] = method_display["Median Total Hari"].round(1)
    st.dataframe(method_display, use_container_width=True, hide_index=True)

    metric = st.selectbox("Metric heatmap", ["SLA Compliance", "Median Hari", "Pass Rate"])
    matrix = method_stage_matrix(pipeline, ids, metric)
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
            use_container_width=True,
            hide_index=True,
        )


elif page == "Sebaran & Penempatan":
    hero(
        "Sebaran Rekrutmen & Penempatan",
        "Bandingkan kebutuhan, hasil kontrak, dan kesesuaian penempatan akhir terhadap rencana.",
    )

    cols = st.columns(4)
    cols[0].metric("Total Kuota", number(quota))
    cols[1].metric("Kontrak", number(signed))
    cols[2].metric("Quota Fulfilment", pct(quota_fulfilment))
    cols[3].metric("Exact Alignment", pct(alignment))

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
    st.dataframe(region_table[["REGION", "QUOTA", "SIGNED", "GAP", "Fulfilment"]], use_container_width=True, hide_index=True)


else:
    hero(
        "Candidate–Position Matching",
        "Identifikasi kandidat yang paling sesuai dengan persyaratan posisi secara transparan.",
    )

    vacancy_options = vacancies.copy()
    if programs:
        vacancy_options = vacancy_options[vacancy_options["NAMA_REKRUTMEN"].isin(programs)]
    if regions:
        vacancy_options = vacancy_options[vacancy_options["REGION"].isin(regions)]
    vacancy_options["LABEL"] = (
        vacancy_options["VACANCY_ID"]
        + " · "
        + vacancy_options["POSITION_NAME"]
        + " · "
        + vacancy_options["LOCATION_PLAN"]
    )
    selected_label = st.selectbox("Pilih vacancy", vacancy_options["LABEL"].tolist())
    selected_vacancy = vacancy_options[vacancy_options["LABEL"].eq(selected_label)].iloc[0]
    pool = st.radio("Candidate pool", ["Lolos Wawancara", "Belum Kontrak", "Semua Pendaftar"], horizontal=True)

    st.markdown(
        f"""
        <div class="insight">
        <b>{selected_vacancy['POSITION_NAME']} — {selected_vacancy['LOCATION_PLAN']}</b><br>
        Unit: {selected_vacancy['UNIT_NAME']} · Kuota: {selected_vacancy['QUOTA']} · Prioritas: {selected_vacancy['VACANCY_PRIORITY']}<br>
        Jenjang: {selected_vacancy['JENJANG_REQUIRED']} · Prodi: {selected_vacancy['PRODI_REQUIRED']}<br>
        Minimum IPK: {selected_vacancy['MIN_IPK']:.2f} · Akding: {selected_vacancy['MIN_AKDING_SCORE']} · Adaptif: {selected_vacancy['MIN_ADAPTIVE_SCORE']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    candidate_source = scoped_apps if (programs or regions or methods) else apps
    scores = score_candidates_for_vacancy(candidate_source, selected_vacancy, pool)
    category_counts = scores["MATCH_CATEGORY"].value_counts()
    cols = st.columns(4)
    cols[0].metric("Candidate Pool", number(len(scores)))
    cols[1].metric("Strong Match", number(category_counts.get("STRONG_MATCH", 0)))
    cols[2].metric("Moderate Match", number(category_counts.get("MODERATE_MATCH", 0)))
    cols[3].metric("Low Match", number(category_counts.get("LOW_MATCH", 0)))

    left, right = st.columns([1, 2])
    with left:
        chart_counts = category_counts.rename_axis("Kategori").reset_index(name="Jumlah")
        fig = px.bar(
            chart_counts,
            x="Kategori",
            y="Jumlah",
            color="Kategori",
            color_discrete_map={"STRONG_MATCH": GREEN, "MODERATE_MATCH": PLN_YELLOW, "LOW_MATCH": RED},
            title="Distribusi Match",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_layout(fig), width="stretch")
    with right:
        st.markdown("### Kandidat Teratas")
        display = scores.head(30).copy()
        display["GPA"] = display["GPA"].round(2)
        st.dataframe(
            display[
                ["ID_PENDAFTARAN", "JENJANG", "PRODI", "GPA", "TOTAL SKOR AKDING", "ADAPTIVE_TOTAL", "MATCH_SCORE", "MATCH_CATEGORY", "MATCH_GAPS"]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        '<p class="small-note">Match score digunakan sebagai decision support. Gender, agama, status pernikahan, nama, alamat, dan identitas pribadi tidak digunakan dalam perhitungan.</p>',
        unsafe_allow_html=True,
    )
