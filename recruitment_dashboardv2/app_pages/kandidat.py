"""Halaman 4 — Kandidat & Pasar Tenaga Kerja.

Pertanyaan yang dijawab: siapa yang melamar ke PLN?
Jangkar: peta volume tes per kota (Plotly scatter_geo). Lihat docs/wireframe.md
Halaman 4 — revisi 2026-08-19: sebaran asal per provinsi, almamater, dan peta
asal-vs-kota-tes DIBATALKAN (kolomnya dibagikan acak seragam oleh generator,
lihat mockdb/ISSUES_SEBARAN.md), diganti data yang sebarannya sudah berpola benar.
"""

from __future__ import annotations

import altair as alt
import plotly.graph_objects as go
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, desimal

ui.judul_halaman("Kandidat & Pasar Tenaga Kerja")

akun = metrics.akun_ringkas()
jenjang = metrics.jenjang_pendidikan()
gender = metrics.gender_per_kohort()
kota = metrics.volume_tes_per_kota_geo()

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Akun", "value": angka(akun["akun"])},
        {"label": "Pelamar unik", "value": angka(akun["pelamar"])},
        {"label": "Lamaran/akun", "value": desimal(akun["lamaran_per_akun"], 2)},
        {"label": "Tidak melamar", "value": angka(akun["tidak_melamar"])},
    ]
)

# ── Blok jangkar: peta volume tes per kota ──────────────────────────────────
top8 = kota.head(8)
warna = theme.warna_seri(0)
t = theme.token()

peta = go.Figure()
peta.add_trace(
    go.Scattergeo(
        lat=kota["lat"],
        lon=kota["lon"],
        mode="markers",
        marker=dict(
            size=kota["n"],
            sizemode="area",
            sizeref=2.0 * kota["n"].max() / (42.0**2),
            sizemin=3,
            color=warna,
            opacity=0.75,
            line=dict(width=0),
        ),
        text=[f"{r.lokasi_kota}: {angka(r.n)} tes" for r in kota.itertuples()],
        hoverinfo="text",
        showlegend=False,
    )
)
peta.add_trace(
    go.Scattergeo(
        lat=top8["lat"],
        lon=top8["lon"],
        mode="text",
        text=[f"{r.lokasi_kota} ({angka(r.n)})" for r in top8.itertuples()],
        textposition="top center",
        textfont=dict(size=11, color=t["text_primary"]),
        hoverinfo="skip",
        showlegend=False,
    )
)
peta.update_geos(
    scope="asia",
    center=dict(lat=-2, lon=118),
    projection_scale=3.4,
    showland=True,
    landcolor=t["surface_page"],
    showcountries=True,
    countrycolor=t["border"],
    showocean=True,
    oceancolor=t["surface_card"],
    showlakes=False,
    bgcolor="rgba(0,0,0,0)",
)
theme.plotly_layout(peta, height=440)

with ui.temuan_halaman("Kota dengan volume tes terbanyak"):
    st.plotly_chart(peta, width="stretch", config={"displayModeBar": False})

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
kiri, kanan = st.columns(2)

with kiri:
    with ui.blok_chart("S1/D-IV mendominasi pelamar"):
        st.altair_chart(
            alt.Chart(jenjang)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=theme.warna_seri(0))
            .encode(
                y=alt.Y("degree:N", sort="-x", title=None),
                x=alt.X("n:Q", title=None),
                tooltip=[
                    alt.Tooltip("degree:N", title="Jenjang"),
                    alt.Tooltip("n:Q", title="Jumlah", format=","),
                ],
            )
            .properties(height=260)
        )

with kanan:
    with ui.blok_chart("Proporsi pria berayun 62-74% per tahun"):
        st.altair_chart(
            alt.Chart(gender)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=theme.warna_seri(0))
            .encode(
                x=alt.X("tahun:O", title=None),
                y=alt.Y("pct_pria:Q", title=None, scale=alt.Scale(domain=[0, 100])),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("n:Q", title="Pelamar", format=","),
                    alt.Tooltip("pct_pria:Q", title="Persen pria", format=".1f"),
                ],
            )
            .properties(height=260)
        )

ui.tentang_halaman(
    "**Sebaran asal per provinsi, analisis almamater, dan peta asal-vs-kota-tes "
    "dibatalkan** — ketiganya bersandar pada `kota_domisili`/`kota_asal`/"
    "`sekolah_universitas`, yang dibagikan acak seragam oleh generator saat ini "
    "(lihat `mockdb/ISSUES_SEBARAN.md`). Peta di atas memakai `lokasi_kota` "
    "(kota tempat tes offline) yang sebarannya sudah diverifikasi berpola benar.\n\n"
    "**PII tidak pernah ditampilkan** di halaman ini maupun lapis analis — seluruh "
    "angka teragregasi."
)

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(
        metrics.rumpun_melamar_vs_diterima(),
        "rumpun_melamar_vs_diterima.csv",
        "Rumpun jurusan: melamar vs diterima",
    )
