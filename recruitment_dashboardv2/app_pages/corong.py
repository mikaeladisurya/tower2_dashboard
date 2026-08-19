"""Halaman 3 — Corong Seleksi.

Pertanyaan yang dijawab: di tahap mana kandidat berguguran, dan kenapa?
Jangkar: Sankey alur gugur (Plotly). Lihat docs/wireframe.md Halaman 3.
"""

from __future__ import annotations

import altair as alt
import plotly.graph_objects as go
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Corong Seleksi")

f = metrics.funnel_seleksi().set_index("tahap_kode")
r = metrics.ringkasan()
ns = metrics.no_show_per_tahap_mode()
rbb = metrics.jejak_rbb()

pendaftaran = r["pendaftaran"]
masuk_akademik = int(f.loc["akademik_inggris", "masuk"])
lulus_adaptif = int(f.loc["adaptif", "lulus"])
rbb_langsung = masuk_akademik - lulus_adaptif  # jalur RBB masuk di tahap akademik, lewati admin+adaptif

no_show_terbesar = ns.iloc[0]

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Pendaftaran", "value": angka(pendaftaran)},
        {"label": "Diterima", "value": angka(r["diterima"])},
        {
            "label": "No-show tertinggi",
            "value": persen(no_show_terbesar["pct_no_show"]),
            "help": f"Tahap {no_show_terbesar['tahap_kode']} ({no_show_terbesar['mode']})",
        },
        {
            "label": "Rasio seleksi",
            "value": persen(100 * r["diterima"] / pendaftaran, 1),
        },
    ]
)

# ── Blok jangkar: Sankey alur gugur ─────────────────────────────────────────
NODE_URUT = [
    "Pendaftaran",
    "Administrasi",
    "Adaptif",
    "Akademik & Inggris",
    "Psikologi",
    "Fisik & MCU",
    "Wawancara",
    "Diterima",
    "Gugur",
]
IDX = {nama: i for i, nama in enumerate(NODE_URUT)}
IDX_GUGUR = IDX["Gugur"]

alur = [
    ("Pendaftaran", "Administrasi", int(f.loc["administrasi", "masuk"])),
    ("Pendaftaran", "Akademik & Inggris", rbb_langsung),
    ("Administrasi", "Adaptif", int(f.loc["administrasi", "lulus"])),
    ("Administrasi", "Gugur", int(f.loc["administrasi", "masuk"] - f.loc["administrasi", "lulus"])),
    ("Adaptif", "Akademik & Inggris", lulus_adaptif),
    ("Adaptif", "Gugur", int(f.loc["adaptif", "masuk"] - f.loc["adaptif", "lulus"])),
    ("Akademik & Inggris", "Psikologi", int(f.loc["akademik_inggris", "lulus"])),
    ("Akademik & Inggris", "Gugur", int(f.loc["akademik_inggris", "masuk"] - f.loc["akademik_inggris", "lulus"])),
    ("Psikologi", "Fisik & MCU", int(f.loc["psikologi", "lulus"])),
    ("Psikologi", "Gugur", int(f.loc["psikologi", "masuk"] - f.loc["psikologi", "lulus"])),
    ("Fisik & MCU", "Wawancara", int(f.loc["fisik_mcu", "lulus"])),
    ("Fisik & MCU", "Gugur", int(f.loc["fisik_mcu", "masuk"] - f.loc["fisik_mcu", "lulus"])),
    ("Wawancara", "Diterima", int(f.loc["wawancara", "lulus"])),
    ("Wawancara", "Gugur", int(f.loc["wawancara", "masuk"] - f.loc["wawancara", "lulus"])),
]

throughput = {nama: 0 for nama in NODE_URUT}
for asal, tujuan, nilai in alur:
    throughput[asal] += nilai
    if tujuan != "Gugur":
        throughput[tujuan] = max(throughput[tujuan], throughput.get(tujuan, 0))
throughput["Pendaftaran"] = pendaftaran
throughput["Gugur"] = sum(v for a, t, v in alur if t == "Gugur")

label_node = [f"{nama}<br>{angka(throughput[nama])}" for nama in NODE_URUT]
warna_seri = theme.seri()
warna_node = [warna_seri[0]] * (len(NODE_URUT) - 1) + [theme.STATUS["kritis"]]
warna_link = [
    "rgba(208,59,59,0.35)" if tujuan == "Gugur" else "rgba(0,119,200,0.35)"
    for _, tujuan, _ in alur
]

sankey = go.Figure(
    go.Sankey(
        arrangement="snap",
        node=dict(
            label=label_node,
            color=warna_node,
            pad=18,
            thickness=16,
            line=dict(width=0),
        ),
        link=dict(
            source=[IDX[a] for a, _, _ in alur],
            target=[IDX[t] for _, t, _ in alur],
            value=[v for _, _, v in alur],
            color=warna_link,
        ),
        textfont=dict(size=13),
    )
)
theme.plotly_layout(sankey, height=440)

with ui.temuan_halaman("Dari pendaftar sampai diterima: enam gerbang, satu jalan keluar"):
    st.plotly_chart(sankey, width="stretch", config={"displayModeBar": False})

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
kiri, kanan = st.columns(2)

with kiri:
    ns_plot = ns.copy()
    ns_plot["label"] = ns_plot["tahap_kode"].map(
        {
            "adaptif": "Adaptif (online)",
            "akademik_inggris": "Akademik (online)",
            "psikologi": "Psikologi (offline)",
            "fisik_mcu": "Fisik (offline)",
            "wawancara": "Wawancara (offline)",
        }
    )
    with ui.blok_chart("Tes online kehilangan separuh pesertanya, tes offline tidak"):
        st.altair_chart(
            alt.Chart(ns_plot)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                y=alt.Y("label:N", sort="-x", title=None),
                x=alt.X("pct_no_show:Q", title=None),
                color=alt.Color(
                    "mode:N",
                    scale=alt.Scale(domain=["online", "offline"], range=theme.seri()[:2]),
                    legend=alt.Legend(title="Mode", orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("label:N", title="Tahap"),
                    alt.Tooltip("pct_no_show:Q", title="Tidak hadir", format=".1f"),
                ],
            )
            .properties(height=260)
        )

with kanan:
    rbb_plot = rbb.melt(
        id_vars=["tahun"], value_vars=["pelamar_fhci", "masuk_pln"],
        var_name="sumber", value_name="jumlah",
    )
    rbb_plot["sumber"] = rbb_plot["sumber"].map({"pelamar_fhci": "FHCI", "masuk_pln": "Sistem PLN"})
    with ui.blok_chart("Jalur RBB nyaris tak berjejak di sistem PLN"):
        st.altair_chart(
            alt.Chart(rbb_plot)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                y=alt.Y("tahun:O", title=None),
                x=alt.X("jumlah:Q", title=None),
                color=alt.Color(
                    "sumber:N",
                    scale=alt.Scale(domain=["FHCI", "Sistem PLN"], range=theme.seri()[:2]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("sumber:N", title="Sumber"),
                    alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
                ],
            )
            .properties(height=260)
        )

ui.tentang_halaman(
    "**Aliran +5.280 masuk langsung di Akademik & Inggris** adalah jalur RBB — kandidat "
    "yang sudah disaring FHCI (lihat blok kanan) masuk sistem PLN pada tahap ini, "
    "melewati Administrasi dan Adaptif yang hanya berlaku untuk jalur mandiri.\n\n"
    "**Corong FHCI** (blok kanan) adalah data ⟨AGREGAT⟩ per tahun program, dari luar "
    "sistem PLN — bukan data per-kandidat, jadi tidak bisa disaring per profesi/kota.\n\n"
    "**No-show online vs offline** (blok kiri) menggantikan hipotesis jarak tempat "
    "tinggal, yang gugur setelah diuji: `kota_domisili` dibagikan acak seragam oleh "
    "generator saat ini (lihat `mockdb/ISSUES_SEBARAN.md`)."
)

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(
        metrics.funnel_seleksi(),
        "corong_seleksi_per_tahap.csv",
        "Corong per tahap (masuk, hadir, lulus, no-show)",
    )
