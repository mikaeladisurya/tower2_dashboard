"""Halaman 6 — Penempatan & Pemenuhan.

Pertanyaan yang dijawab: rencana mendarat di mana, dan seberapa tepat?
Jangkar: treemap unit x bidang (Plotly). Lihat docs/wireframe.md Halaman 6.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Penempatan & Pemenuhan")

jenis = metrics.penempatan_jenis().set_index("jenis_penempatan")["jumlah"]
grade = metrics.grade_masuk()
rencana = metrics.rencana_vs_realisasi()
treemap_df = metrics.treemap_penempatan()

ditempatkan = int(jenis.sum())
induk = int(jenis.get("INDUK", 0))
subholding = int(jenis.get("SUBHOLDING", 0))
grade_top = grade.iloc[0]

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Ditempatkan", "value": angka(ditempatkan)},
        {"label": "Induk", "value": f"{angka(induk)} ({persen(100 * induk / ditempatkan, 0)})"},
        {"label": "Subholding", "value": f"{angka(subholding)} ({persen(100 * subholding / ditempatkan, 0)})"},
        {
            "label": f"Grade {grade_top['kode_grade']}",
            "value": f"{angka(grade_top['n'])} ({persen(100 * grade_top['n'] / grade['n'].sum(), 0)})",
        },
    ]
)

# ── Blok jangkar: treemap unit x bidang ─────────────────────────────────────
unit_teratas = treemap_df.groupby("unit_induk")["n"].sum().idxmax()

treemap_fig = px.treemap(
    treemap_df,
    path=["unit_induk", "bidang_pembidangan"],
    values="n",
    color_discrete_sequence=theme.seri(),
)
treemap_fig.update_traces(textinfo="label+value")
theme.plotly_layout(treemap_fig, height=440)

with ui.temuan_halaman(f"{unit_teratas} menyerap penempatan terbanyak"):
    st.plotly_chart(treemap_fig, width="stretch", config={"displayModeBar": False})

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
kiri, kanan = st.columns(2)

with kiri:
    slope = pd.concat(
        [
            rencana.assign(sisi="Kuota", nilai=rencana["kuota"]),
            rencana.assign(sisi="Realisasi", nilai=rencana["realisasi"]),
        ],
        ignore_index=True,
    )
    with ui.blok_chart("Rencana vs realisasi: mandiri selalu 100%, RBB bervariasi"):
        st.altair_chart(
            alt.Chart(slope)
            .mark_line(point=True)
            .encode(
                x=alt.X("sisi:N", sort=["Kuota", "Realisasi"], title=None),
                y=alt.Y("nilai:Q", title=None),
                detail="tahun:N",
                color=alt.Color(
                    "jalur:N",
                    scale=alt.Scale(domain=["mandiri", "rbb"], range=theme.seri()[:2]),
                    legend=alt.Legend(title="Jalur", orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("tahun:N", title="Tahun"),
                    alt.Tooltip("jalur:N", title="Jalur"),
                    alt.Tooltip("kuota:Q", title="Kuota", format=","),
                    alt.Tooltip("realisasi:Q", title="Realisasi", format=","),
                    alt.Tooltip("pct:Q", title="Pemenuhan", format=".1f"),
                ],
            )
            .properties(height=280)
        )

with kanan:
    label_grade = {"G1": "G1 (SMK/D3)", "G2": "G2 (S1/D4)", "G3": "G3 (S2)"}
    grade_plot = grade.copy()
    grade_plot["label"] = grade_plot["kode_grade"].map(label_grade)
    with ui.blok_chart("Grade masuk sesuai jenjang pendidikan"):
        st.altair_chart(
            alt.Chart(grade_plot)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=theme.warna_seri(0))
            .encode(
                y=alt.Y("label:N", sort="-x", title=None),
                x=alt.X("n:Q", title=None),
                tooltip=[
                    alt.Tooltip("label:N", title="Grade"),
                    alt.Tooltip("n:Q", title="Jumlah", format=","),
                ],
            )
            .properties(height=280)
        )

ui.tentang_halaman(
    "**Tiga tahun RBB** (2020, 2021, 2024) sengaja bervariasi jauh dari 100% — kuotanya "
    "kohort penuh dari FHCI, sementara `realisasi` hanya menghitung yang sudah tercatat "
    "serah-terima di sistem PLN. Membacanya sebagai kegagalan target itu keliru.\n\n"
    "**Grade masuk** G1/G2/G3 mengikuti jenjang pendidikan pelamar (SMK/D3 → G1, "
    "S1/D4 → G2, S2 → G3) — sudah tervalidasi konsisten dengan aturan penempatan."
)

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(
        treemap_df,
        "penempatan_per_unit_bidang.csv",
        "Penempatan per unit induk x bidang",
    )
