"""Halaman 2 — Perencanaan Kebutuhan.

Pertanyaan yang dijawab: berapa orang yang perlu direkrut, dan di unit mana?
Seluruh halaman DIMODELKAN — tidak ada kuota per posisi di sistem PLN manapun.
Lihat docs/wireframe.md Halaman 2.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Perencanaan Kebutuhan")

gap = metrics.gap_ftk()
proyeksi = metrics.proyeksi_per_sebab()
pagu = metrics.pagu_vs_usulan()
gap_unit = metrics.gap_ftk_per_unit()

kekosongan_2026 = int(proyeksi.loc[proyeksi["tahun"] == 2026, "total"].iloc[0])
usulan_2025 = int(pagu.loc[pagu["tahun"] == 2025, "usulan"].iloc[0])
pagu_2025 = pagu.loc[pagu["tahun"] == 2025, "pct_disetujui"].iloc[0]

ui.spanduk_dimodelkan(
    "Tidak ada satu pun angka kuota per posisi di sistem PLN manapun — halaman ini "
    "memperagakan insight yang bisa muncul kalau data itu dikumpulkan. Satu-satunya "
    "bahan nyata: kolom FTK & realisasi di `unit_induk`."
)

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Gap FTK 2026", "value": angka(gap["gap"])},
        {"label": "Kekosongan 2026", "value": angka(kekosongan_2026)},
        {"label": "Usulan 2025", "value": angka(usulan_2025)},
        {"label": "Pagu disetujui 2025", "value": persen(pagu_2025)},
    ]
)

# ── Blok jangkar: persetujuan pagu per tahun ────────────────────────────────
with ui.temuan_halaman(
    f"Persetujuan pagu naik dari {persen(pagu.iloc[0]['pct_disetujui'])} "
    f"({int(pagu.iloc[0]['tahun'])}) jadi {persen(pagu_2025)} (2025)"
):
    st.altair_chart(
        alt.Chart(pagu)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=theme.warna_seri(0))
        .encode(
            x=alt.X("tahun:O", title=None),
            y=alt.Y("pct_disetujui:Q", title=None),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("usulan:Q", title="Usulan", format=","),
                alt.Tooltip("pagu:Q", title="Pagu", format=","),
                alt.Tooltip("pct_disetujui:Q", title="Disetujui", format=".1f"),
            ],
        )
        .properties(height=260)
    )

# ── Dua blok pendukung (maks 2, D5) ──────────────────────────────────────────
kiri, kanan = st.columns(2)

with kiri:
    proyeksi_plot = proyeksi.melt(
        id_vars=["tahun"],
        value_vars=["pensiun", "aps", "meninggal", "phk"],
        var_name="sebab",
        value_name="jumlah",
    )
    label_sebab = {"pensiun": "Pensiun", "aps": "Mengundurkan diri", "meninggal": "Meninggal", "phk": "PHK"}
    proyeksi_plot["sebab"] = proyeksi_plot["sebab"].map(label_sebab)
    with ui.blok_chart("Pensiun mendominasi kekosongan"):
        st.altair_chart(
            alt.Chart(proyeksi_plot)
            .mark_bar()
            .encode(
                x=alt.X("tahun:O", title=None),
                y=alt.Y("jumlah:Q", title=None, stack="zero"),
                color=alt.Color(
                    "sebab:N",
                    scale=alt.Scale(domain=list(label_sebab.values()), range=theme.seri()[:4]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("sebab:N", title="Sebab"),
                    alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
                ],
            )
            .properties(height=280)
        )

with kanan:
    top10 = gap_unit.head(10).sort_values("gap")
    with ui.blok_chart(f"Gap FTK terbesar: {gap_unit.iloc[0]['nama_pendek']}"):
        st.altair_chart(
            alt.Chart(top10)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=theme.warna_seri(0))
            .encode(
                y=alt.Y("nama_pendek:N", sort=None, title=None),
                x=alt.X("gap:Q", title=None),
                tooltip=[
                    alt.Tooltip("nama_pendek:N", title="Unit"),
                    alt.Tooltip("ftk_2025:Q", title="FTK 2025", format=","),
                    alt.Tooltip("realisasi_mar_2026:Q", title="Realisasi", format=","),
                    alt.Tooltip("gap:Q", title="Gap", format=","),
                ],
            )
            .properties(height=280)
        )

ui.tentang_halaman(
    "**Gap FTK** = `ftk_2025 − realisasi_mar_2026`, dijumlah per unit induk. "
    "Kolom `realisasi_apr_2026` sengaja tidak dipakai — hanya terisi di 1 dari 48 unit.\n\n"
    "**UID Jawa Tengah & DIY dikeluarkan** dari peringkat gap per unit (blok kanan) — "
    "unit ini punya baris master data anomali (`jumlah_pegawai=4`, lihat "
    "`mockdb/ISSUES_MASTER_DATA.md`), difilter dengan `jumlah_pegawai > 50`.\n\n"
    "**Kekosongan, usulan, dan pagu** seluruhnya DIMODELKAN — tidak ditarik dari sistem "
    "kepegawaian PLN yang sebenarnya."
)

# ── Lapis analis: heatmap unit × sub-bidang, dipindah dari rencana blok jangkar lama ──
if ui.mode_analis():
    heatmap = metrics.heatmap_kebutuhan(2025)
    st.markdown("**Usulan kebutuhan 2025: unit induk × sub-bidang**")
    st.altair_chart(
        alt.Chart(heatmap)
        .mark_rect()
        .encode(
            x=alt.X("sub_bidang:N", title=None),
            y=alt.Y("unit_induk:N", title=None),
            color=alt.Color("usulan:Q", scale=alt.Scale(scheme="blues"), title="Usulan"),
            tooltip=[
                alt.Tooltip("unit_induk:N", title="Unit"),
                alt.Tooltip("sub_bidang:N", title="Sub-bidang"),
                alt.Tooltip("usulan:Q", title="Usulan", format=","),
            ],
        )
        .properties(height=520)
    )
    ui.lapis_analis(gap_unit, "gap_ftk_per_unit.csv", "Gap FTK per unit induk")
