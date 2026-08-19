"""Halaman 1 — Ringkasan.

Pertanyaan yang dijawab: sehat tidak mesin rekrutmen kita?
Ditulis ulang 2026-08-19 di bawah doktrin D1-D6 (docs/design_system.md §11) —
lihat docs/wireframe.md untuk wireframe blok-per-blok.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, persen, rasio

TAHUN_RBB = {2020, 2021, 2024}

ui.judul_halaman("Ringkasan")

r = metrics.ringkasan()
tren = metrics.tren_tahunan()
pipeline = metrics.posisi_pipeline()
funnel = metrics.funnel_seleksi()
gugur = metrics.gugur_per_tahap().set_index("tahap_gugur")["gugur"]

# ── Baris KPI (native, tanpa badge — D4) ────────────────────────────────────
ui.baris_kpi(
    [
        {
            "label": "Pendaftaran",
            "value": angka(r["pendaftaran"]),
            "help": f"{angka(r['pelamar'])} pelamar unik",
            "chart_data": tren.groupby("tahun")["pendaftaran"].sum().tolist(),
        },
        {
            "label": "Diterima",
            "value": angka(r["diterima"]),
            "help": "Dari 7 kohort gelombang 2019-2025",
            "chart_data": tren.groupby("tahun")["diterima"].sum().tolist(),
        },
        {
            "label": "Rasio seleksi",
            "value": rasio(r["rasio"]),
            "help": f"{persen(100 * r['diterima'] / r['pendaftaran'], 1)} pendaftaran berujung diterima",
        },
        {
            "label": "Sudah ber-SK",
            "value": angka(r["sudah_sk"]),
            "help": (
                f"+{angka(r['sedang_ojt'])} sedang OJT — selisih dari {angka(r['diterima'])} "
                "diterima bukan data hilang, itu pipeline yang sedang berjalan"
            ),
        },
    ]
)

# ── Blok jangkar: satu kalimat temuan halaman (D1+D3) ───────────────────────
funnel_urut = funnel.sort_values("urutan")
with ui.temuan_halaman(
    f"Tes Adaptif menggugurkan {angka(gugur.get('adaptif'))} orang — "
    f"lebih banyak daripada seleksi administrasi ({angka(gugur.get('administrasi'))})"
):
    tahap_urutan = funnel_urut["nama"].tolist() + ["Diterima"]
    funnel_plot = funnel_urut[["nama", "masuk"]].rename(columns={"masuk": "jumlah"})
    funnel_plot = pd.concat(
        [funnel_plot, pd.DataFrame([{"nama": "Diterima", "jumlah": r["diterima"]}])],
        ignore_index=True,
    )
    st.altair_chart(
        alt.Chart(funnel_plot)
        .mark_bar(
            cornerRadiusTopRight=4,
            cornerRadiusBottomRight=4,
            color=theme.warna_seri(0),
        )
        .encode(
            y=alt.Y("nama:N", sort=tahap_urutan, title=None),
            x=alt.X("jumlah:Q", title=None),
            tooltip=[
                alt.Tooltip("nama:N", title="Tahap"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=260)
    )

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
skala_jalur = alt.Scale(domain=["mandiri", "rbb"], range=theme.seri()[:2])
warna_jalur = alt.Color(
    "jalur:N", scale=skala_jalur, legend=alt.Legend(title="Jalur", orient="top")
)

kiri, kanan = st.columns(2)

with kiri:
    with ui.blok_chart("Pendaftaran per tahun"):
        st.altair_chart(
            alt.Chart(tren)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("tahun:O", title=None),
                y=alt.Y("pendaftaran:Q", title=None),
                color=warna_jalur,
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("jalur:N", title="Jalur"),
                    alt.Tooltip("pendaftaran:Q", title="Pendaftaran", format=","),
                ],
            )
            .properties(height=280)
        )

with kanan:
    pipa = pipeline.melt(
        id_vars=["nama", "urutan"],
        value_vars=["selesai", "berjalan"],
        var_name="status",
        value_name="jumlah",
    )
    pipa = pipa[pipa["jumlah"] > 0]
    with ui.blok_chart(f"{angka(r['sedang_ojt'])} orang kohort 2025 sedang OJT"):
        st.altair_chart(
            alt.Chart(pipa)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                y=alt.Y("nama:N", sort=alt.SortField("urutan"), title=None),
                x=alt.X("jumlah:Q", title=None),
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(
                        domain=["selesai", "berjalan"],
                        range=[theme.warna_seri(0), theme.STATUS["peringatan"]],
                    ),
                    legend=alt.Legend(title="Status", orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("nama:N", title="Tahap"),
                    alt.Tooltip("status:N", title="Status"),
                    alt.Tooltip("jumlah:Q", title="Orang", format=","),
                ],
            )
            .properties(height=280)
        )

ui.tentang_halaman(
    "**Diterima** ≠ **sudah jadi pegawai.** Kolom `hasil_akhir = 'DITERIMA'` berarti "
    "lulus seluruh tahap seleksi; `status_sk = 'SUDAH'` berarti sudah SK pengangkatan. "
    "Selisih keduanya adalah kandidat yang sedang OJT pada tanggal potong 15 September 2026.\n\n"
    "**Tahun jalur RBB** (2020, 2021, 2024) tidak sebanding langsung dengan tahun mandiri — "
    "pendaftaran RBB yang tercatat di sistem PLN hanya yang sudah lolos saringan FHCI."
)

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    rinci = metrics.rencana_vs_realisasi().merge(
        tren.drop(columns=["jalur"]), on="tahun", how="left"
    )
    rinci["catatan"] = rinci["tahun"].apply(
        lambda t: "RBB — kuota = kohort penuh, yang tercatat di PLN hanya pasca-FHCI"
        if t in TAHUN_RBB
        else ""
    )
    ui.lapis_analis(
        rinci[["tahun", "jalur", "pendaftaran", "diterima", "kuota", "pct", "catatan"]],
        "ringkasan_kohort.csv",
        "Ringkasan per kohort",
    )
