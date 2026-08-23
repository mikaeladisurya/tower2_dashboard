"""Halaman 2 -- Perencanaan Formasi.

Pertanyaan harian: berapa yang akan kosong, di mana, jabatan apa? Rantai data:
proyeksi kekosongan (per unit x posisi, 2019-2026) -> usulan unit (kekosongan +
gap FTK) -> pagu disetujui (2019-2025). Lihat docs/RANCANGAN_HALAMAN.md §4.

`proyeksi_kekosongan` berhenti di tahun terakhirnya -- begitu `hari_ini()`
melewatinya, blok tahun-berjalan menampilkan keadaan data apa adanya lalu jatuh
ke tahun historis terakhir, bukan galat dan bukan angka lama yang disamarkan.
"""

from __future__ import annotations

from datetime import date

import altair as alt
import streamlit as st

from components.tampilan import keadaan_kosong, tinggi_kontainer
from core import db, metrics
from core.format import angka

_LABEL_SEBAB = {
    "pensiun": "Pensiun",
    "mengundurkan_diri": "Mengundurkan Diri",
    "meninggal_dunia": "Meninggal Dunia",
    "phk": "PHK",
}

st.title("Perencanaan Formasi")

acuan = db.hari_ini()
tahun_min_data, tahun_maks_data = metrics.rentang_tahun_proyeksi()
tahun_tampil = min(acuan.year, tahun_maks_data)

# ── Blok 1: kekosongan per posisi & sub-bidang, per unit terpilih ───────────
st.subheader("Kekosongan per Posisi & Sub-Bidang")

daftar_unit = metrics.daftar_unit_induk()
_nama_per_kode = daftar_unit.set_index("kode_unit")["nama_pendek"]
unit_terpilih = st.selectbox(
    "Unit induk",
    options=daftar_unit["kode_unit"],
    format_func=lambda kode: _nama_per_kode.loc[kode],
)

posisi = metrics.kekosongan_per_posisi(unit_terpilih, tahun_tampil)
if posisi.empty:
    keadaan_kosong("Tidak ada posisi kosong di unit")
else:
    with st.container(key="kekosongan_posisi"):
        st.dataframe(
            posisi,
            column_config={
                "nama_posisi": st.column_config.TextColumn("Posisi"),
                "sub_bidang": st.column_config.TextColumn("Sub-Bidang"),
                "jenjang": st.column_config.TextColumn("Jenjang"),
                "kekosongan": st.column_config.NumberColumn(
                    "Kekosongan", format="localized"
                ),
            },
            hide_index=True,
            width="stretch",
        )
    tinggi_kontainer("kekosongan_posisi", offset_px=420)

# ── Blok 2: gap FTK per unit ─────────────────────────────────────────────────
st.subheader("Gap FTK per Unit Induk")

gap_nasional = metrics.gap_ftk_nasional()
with st.container(border=True, horizontal=True):
    st.metric(
        "Formasi (FTK)",
        angka(gap_nasional["ftk"]),
        help="Formasi tenaga kerja yang ditetapkan untuk tahun 2025.",
        icon=":material/badge:",
    )
    st.metric(
        "Realisasi",
        angka(gap_nasional["realisasi"]),
        help="Jumlah pegawai riil per Maret 2026.",
        icon=":material/groups:",
    )
    st.metric(
        "Gap",
        angka(gap_nasional["gap"]),
        help="Formasi dikurangi realisasi -- kekurangan pegawai terhadap formasi yang ditetapkan.",
        icon=":material/trending_down:",
    )

gap_unit = metrics.gap_ftk_per_unit()
if gap_unit.empty:
    keadaan_kosong("Tidak ada data gap FTK")
else:
    _chart_gap = (
        alt.Chart(gap_unit)
        .mark_bar()
        .encode(
            x=alt.X("gap:Q", title="Gap FTK"),
            y=alt.Y("nama_pendek:N", sort="-x", title="Unit Induk"),
            tooltip=[
                alt.Tooltip("nama_pendek:N", title="Unit Induk"),
                alt.Tooltip("jenis_unit:N", title="Jenis Unit"),
                alt.Tooltip("ftk_2025:Q", title="Formasi (FTK)"),
                alt.Tooltip("realisasi_mar_2026:Q", title="Realisasi"),
                alt.Tooltip("gap:Q", title="Gap"),
            ],
        )
        .properties(height=max(320, 18 * len(gap_unit)))
    )
    st.altair_chart(_chart_gap, width="stretch")

# ── Blok 3: usulan vs pagu per tahun ─────────────────────────────────────────
st.subheader("Usulan vs Pagu per Tahun")

usulan_pagu = metrics.usulan_vs_pagu()
if usulan_pagu.empty:
    keadaan_kosong("Tidak ada data usulan dan pagu")
else:
    _up_panjang = usulan_pagu.melt(
        id_vars="tahun",
        value_vars=["usulan", "pagu"],
        var_name="jenis",
        value_name="jumlah",
    )
    _up_panjang["jenis"] = _up_panjang["jenis"].map({"usulan": "Usulan Unit", "pagu": "Pagu Disetujui"})
    _chart_up = (
        alt.Chart(_up_panjang)
        .mark_bar()
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            xOffset=alt.XOffset("jenis:N", title="Jenis"),
            y=alt.Y("jumlah:Q", title="Jumlah"),
            color=alt.Color("jenis:N", title="Jenis"),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("jenis:N", title="Jenis"),
                alt.Tooltip("jumlah:Q", title="Jumlah"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(_chart_up, width="stretch")
    st.dataframe(
        usulan_pagu,
        column_config={
            "tahun": st.column_config.NumberColumn("Tahun", format="%d"),
            "pagu": st.column_config.NumberColumn("Pagu Disetujui", format="localized"),
            "usulan": st.column_config.NumberColumn("Usulan Unit", format="localized"),
            "pct_disetujui": st.column_config.NumberColumn("Persen Disetujui", format="%.1f%%"),
        },
        hide_index=True,
        width="stretch",
    )

# ── Blok 4: kekosongan tahun berjalan & tahun berikutnya per sebab ──────────
st.subheader("Kekosongan per Sebab")

sebab = metrics.kekosongan_per_sebab(acuan=acuan)
if sebab.empty:
    keadaan_kosong(
        f"Proyeksi tahun {acuan.year} belum tersedia",
        terakhir=f"Tahun terakhir tersedia: {tahun_maks_data}",
    )
    sebab = metrics.kekosongan_per_sebab(acuan=date(tahun_maks_data - 1, 1, 1))

if not sebab.empty:
    _sebab_panjang = sebab.melt(
        id_vars="tahun",
        value_vars=list(_LABEL_SEBAB),
        var_name="sebab",
        value_name="jumlah",
    )
    _sebab_panjang["sebab"] = _sebab_panjang["sebab"].map(_LABEL_SEBAB)
    _chart_sebab = (
        alt.Chart(_sebab_panjang)
        .mark_bar()
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            xOffset=alt.XOffset("sebab:N", title="Sebab"),
            y=alt.Y("jumlah:Q", title="Kekosongan"),
            color=alt.Color("sebab:N", title="Sebab"),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("sebab:N", title="Sebab"),
                alt.Tooltip("jumlah:Q", title="Kekosongan"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(_chart_sebab, width="stretch")

# ── Blok 5: kekosongan per unit induk ────────────────────────────────────────
st.subheader(f"Kekosongan per Unit Induk {tahun_tampil}")

per_unit = metrics.kekosongan_per_unit(tahun_tampil)
if per_unit.empty:
    keadaan_kosong(f"Kekosongan tahun {tahun_tampil} tidak tersedia")
else:
    _chart_unit = (
        alt.Chart(per_unit)
        .mark_bar()
        .encode(
            x=alt.X("kekosongan:Q", title="Kekosongan"),
            y=alt.Y("nama_pendek:N", sort="-x", title="Unit Induk"),
            tooltip=[
                alt.Tooltip("nama_pendek:N", title="Unit Induk"),
                alt.Tooltip("jenis_unit:N", title="Jenis Unit"),
                alt.Tooltip("kekosongan:Q", title="Kekosongan"),
            ],
        )
        .properties(height=max(320, 18 * len(per_unit)))
    )
    st.altair_chart(_chart_unit, width="stretch")
