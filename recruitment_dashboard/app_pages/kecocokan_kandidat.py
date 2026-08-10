from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_common import GREEN, PLN_YELLOW, RED, chart_layout, get_ctx, hero, number
from data_layer import score_candidates_for_vacancy

ctx = get_ctx()
all_apps = ctx["all_apps"]
vacancies = ctx["vacancies"]
scoped_apps = ctx["scoped_apps"]
programs = ctx["programs"]
regions = ctx["regions"]
methods = ctx["methods"]

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

candidate_source = scoped_apps if (programs or regions or methods) else all_apps
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
        width="stretch",
        hide_index=True,
    )

st.markdown(
    '<p class="small-note">Match score digunakan sebagai decision support. Gender, agama, status pernikahan, nama, alamat, dan identitas pribadi tidak digunakan dalam perhitungan.</p>',
    unsafe_allow_html=True,
)
