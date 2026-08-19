"""Halaman 5 — Pasca-Seleksi & OJT.

Pertanyaan yang dijawab: siapa yang sedang dalam perjalanan menuju SK?
Jangkar: rantai 7 tahap pasca-seleksi (Altair). Lihat docs/wireframe.md Halaman 5.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka

ui.judul_halaman("Pasca-Seleksi & OJT")

r = metrics.ringkasan()
pipeline = metrics.posisi_pipeline()
timeline = metrics.timeline_kohort()
bidang = metrics.pembidangan()
updl = metrics.sebaran_updl()

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Diterima", "value": angka(r["diterima"])},
        {"label": "Sudah ber-SK", "value": angka(r["sudah_sk"])},
        {"label": "Sedang OJT", "value": angka(r["sedang_ojt"])},
        {"label": "UPDL aktif", "value": angka(len(updl))},
    ]
)

# ── Blok jangkar: rantai 7 tahap pasca-seleksi ──────────────────────────────
pipa = pipeline.melt(
    id_vars=["nama", "urutan"], value_vars=["selesai", "berjalan"],
    var_name="status", value_name="jumlah",
)
pipa = pipa[pipa["jumlah"] > 0]

with ui.temuan_halaman(f"{angka(r['sedang_ojt'])} orang kohort 2025 sedang OJT, SK menyusul"):
    st.altair_chart(
        alt.Chart(pipa)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("nama:N", sort=alt.SortField("urutan"), title=None),
            x=alt.X("jumlah:Q", title=None),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=["selesai", "berjalan"], range=[theme.warna_seri(0), theme.STATUS["peringatan"]]),
                legend=alt.Legend(title="Status", orient="top"),
            ),
            tooltip=[
                alt.Tooltip("nama:N", title="Tahap"),
                alt.Tooltip("status:N", title="Status"),
                alt.Tooltip("jumlah:Q", title="Orang", format=","),
            ],
        )
        .properties(height=300)
    )

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
kiri, kanan = st.columns(2)

with kiri:
    timeline_plot = timeline.copy()
    timeline_plot["status"] = timeline_plot["tahun"].apply(
        lambda t: "berjalan" if t == 2025 else "selesai"
    )
    with ui.blok_chart("Timeline kohort 2019-2025"):
        st.altair_chart(
            alt.Chart(timeline_plot)
            .mark_bar(height=14, cornerRadius=4)
            .encode(
                y=alt.Y("tahun:O", title=None),
                x=alt.X("mulai:T", title=None),
                x2="selesai:T",
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(domain=["selesai", "berjalan"], range=[theme.warna_seri(0), theme.STATUS["peringatan"]]),
                    legend=alt.Legend(title="Status", orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("mulai:T", title="Mulai"),
                    alt.Tooltip("selesai:T", title="Selesai gelombang"),
                    alt.Tooltip("n_gelombang:Q", title="Jumlah gelombang"),
                ],
            )
            .properties(height=280)
        )

with kanan:
    with ui.blok_chart(f"{bidang.iloc[0]['bidang_pembidangan']} menyerap paling banyak"):
        st.altair_chart(
            alt.Chart(bidang)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=theme.warna_seri(0))
            .encode(
                y=alt.Y("bidang_pembidangan:N", sort="-x", title=None),
                x=alt.X("n:Q", title=None),
                tooltip=[
                    alt.Tooltip("bidang_pembidangan:N", title="Bidang"),
                    alt.Tooltip("n:Q", title="Jumlah", format=","),
                ],
            )
            .properties(height=280)
        )

ui.tentang_halaman(
    "**Timeline kohort** (blok kiri) menandai rentang buka-tutup gelombang pendaftaran, "
    "bukan tanggal SK — kohort 2025 masih berjalan karena 2.000 orangnya sedang OJT.\n\n"
    "**Tidak ada analisis durasi/SLA.** Lama tiap tahap pasca-seleksi digenerate konstan "
    "(± 400 hari dari pengumuman ke SK) — belum ada variasi nyata untuk dianalisis."
)

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(updl, "sebaran_updl.csv", "Sebaran penempatan per UPDL")
