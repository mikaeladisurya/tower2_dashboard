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
from core.db import TANGGAL_POTONG
from core.format import angka, persen

ui.judul_halaman("Kandidat & Pasar Tenaga Kerja")

akun = metrics.akun_ringkas()
akun_baru = metrics.akun_baru()
kelengkapan = metrics.kelengkapan_akun()
jenjang = metrics.jenjang_pendidikan()
piramida = metrics.umur_gender()
kota = metrics.volume_tes_per_kota_geo()
pendaftar_bulanan = metrics.pendaftar_per_bulan()

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {
            "label": "Pelamar / Akun",
            "value": f"{angka(akun['pelamar'])} / {angka(akun['akun'])}",
            "help": (
                f"{persen(akun['pelamar'] / akun['akun'] * 100)} akun pernah melamar "
                f"minimal satu lowongan; sisanya ({angka(akun['tidak_melamar'])}) baru "
                "bikin akun."
            ),
        },
        {
            "label": f"Akun baru ({akun_baru['hari']} hari)",
            "value": angka(akun_baru["n"]),
            "help": (
                f"Akun terdaftar dalam {akun_baru['hari']} hari terakhir sampai "
                f"{TANGGAL_POTONG.strftime('%d %B %Y')}. "
                + (
                    f"Nol karena tidak ada gelombang dibuka — gelombang terakhir "
                    f"tutup {akun_baru['hari_sejak_gelombang_tutup']} hari lalu."
                    if akun_baru["n"] == 0 and not akun_baru["gelombang_aktif"]
                    else f"Lamaran masuk periode sama: {angka(akun_baru['lamaran'])}."
                )
            ),
        },
        {
            "label": "Belum aktivasi surel",
            "value": angka(kelengkapan["email_belum_aktif"]),
            "help": (
                "Akun yang belum aktivasi surel — semuanya juga belum pernah melamar, "
                "karena tanpa aktivasi tidak bisa lanjut apply."
            ),
        },
        {
            "label": "Biodata belum lengkap",
            "value": angka(kelengkapan["biodata_belum_lengkap"]),
            "help": (
                "Alamat domisili belum diisi. Kelompok ini beda dari 'belum aktivasi "
                "surel' — sebagian besar surelnya justru sudah aktif."
            ),
        },
        {
            "label": "Profil lengkap & aktif",
            "value": angka(kelengkapan["lengkap_dan_aktif"]),
            "help": (
                "Surel aktif DAN alamat domisili terisi — akun yang datanya siap "
                "diproses lebih lanjut."
            ),
        },
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
    peta_col, jenjang_col = st.columns([2, 1])
    with peta_col:
        st.plotly_chart(peta, width="stretch", config={"displayModeBar": False})
    with jenjang_col:
        st.markdown("**S1/D-IV mendominasi pelamar**")
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
            .properties(height=440)
        )

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
kiri, kanan = st.columns(2)

with kiri:
    with ui.blok_chart("Pendaftaran bergelombang, bukan mengalir rata"):
        st.altair_chart(
            alt.Chart(pendaftar_bulanan)
            .mark_area(color=theme.warna_seri(0), opacity=0.85, line=True)
            .encode(
                x=alt.X("bulan:T", title=None),
                y=alt.Y("n:Q", title=None),
                tooltip=[
                    alt.Tooltip("bulan:T", title="Bulan", format="%b %Y"),
                    alt.Tooltip("n:Q", title="Pendaftaran", format=","),
                ],
            )
            .properties(height=260)
        )

with kanan:
    piramida = piramida.copy()
    piramida["gender_label"] = piramida["jenis_kelamin"].map({"P": "Pria", "W": "Wanita"})
    piramida["nilai"] = piramida["n"].where(piramida["jenis_kelamin"] == "W", -piramida["n"])
    batas = int(piramida["n"].max() * 1.1)

    with ui.blok_chart("Pelamar pria dua kali lipat wanita di tiap umur"):
        st.altair_chart(
            alt.Chart(piramida)
            .mark_bar()
            .encode(
                y=alt.Y("umur:O", sort=alt.SortField("umur", order="descending"), title=None),
                x=alt.X(
                    "nilai:Q",
                    title=None,
                    scale=alt.Scale(domain=[-batas, batas]),
                    axis=alt.Axis(labelExpr="abs(datum.value)"),
                ),
                color=alt.Color(
                    "gender_label:N",
                    scale=alt.Scale(domain=["Pria", "Wanita"], range=[theme.warna_seri(0), theme.warna_seri(1)]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("umur:O", title="Umur"),
                    alt.Tooltip("gender_label:N", title="Gender"),
                    alt.Tooltip("n:Q", title="Jumlah", format=","),
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
