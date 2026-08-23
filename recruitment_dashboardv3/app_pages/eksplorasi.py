"""Halaman Eksplorasi -- fitur yang jelas berguna bagi tim rekrutmen, tapi
sumber datanya belum ada di basis data sungguhan.

Penyimpangan P9 dari pola halaman berdata nyata (G10-G16): halaman-halaman
itu hanya boleh menyajikan angka yang sudah dipanggil lewat `core/metrics.py`
hasil kueri ke basis data sungguhan. Di sini nyaris semua isinya dibangun
dari `core/eksplorasi_sintetis.py` -- angka acak berbenih tetap, bukan hasil
kueri -- karena memang belum ada sumber data sungguhan untuk fitur-fitur ini
(lihat `docs/USULAN_DATABASE.md`). Pola "halaman tidak menulis SQL" tetap
dipegang teguh (tidak ada satu pemanggilan SQL langsung di berkas ini), tapi
alasan memanggil modul sintetis alih-alih `core/metrics.py` untuk sebagian
besar angka adalah karena datanya memang belum pernah ada di basis mana pun.

Satu bagian bercampur: bagian kedua (proyeksi kekosongan) memakai angka
nyata 2019-2026 lewat `core/metrics.py` sebagai jangkar, lalu diekstrapolasi
secara sintetis untuk tahun-tahun sesudahnya -- dijelaskan di tempatnya.

Seluruh isi halaman ini ilustratif dan ditandai demikian di puncak halaman.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from core import eksplorasi_sintetis as sintetis
from core import metrics
from core.format import angka, persen

st.title("Eksplorasi")

st.info(
    "Data ilustratif -- fitur ini menunggu sumber data sungguhan.",
    icon=":material/science:",
)

tab_3t, tab_proyeksi, tab_kompetensi, tab_skor, tab_karier, tab_sumber, tab_updl, tab_biaya = (
    st.tabs(
        [
            "Pemenuhan 3T",
            "Proyeksi Kekosongan",
            "Kompetensi Jabatan",
            "Skor & Kelulusan",
            "Peristiwa Karier",
            "Sumber Rekrutmen",
            "SAMAPTA & UPDL",
            "Biaya Rekrutmen",
        ]
    )
)

# ── Tab 1: Pemenuhan 3T ──────────────────────────────────────────────────────
with tab_3t:
    st.subheader("Pemenuhan Formasi Wilayah 3T")
    df_3t = sintetis.pemenuhan_wilayah_3t()
    panjang_3t = df_3t.melt(
        id_vars="wilayah", value_vars=["rencana", "realisasi"], var_name="jenis", value_name="jumlah"
    )
    panjang_3t["jenis"] = panjang_3t["jenis"].map({"rencana": "Rencana", "realisasi": "Realisasi"})
    chart_3t = (
        alt.Chart(panjang_3t)
        .mark_bar()
        .encode(
            x=alt.X("wilayah:N", title="Wilayah"),
            xOffset=alt.XOffset("jenis:N", title="Jenis"),
            y=alt.Y("jumlah:Q", title="Jumlah OJT"),
            color=alt.Color("jenis:N", title="Jenis"),
            tooltip=[
                alt.Tooltip("wilayah:N", title="Wilayah"),
                alt.Tooltip("jenis:N", title="Jenis"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart_3t, width="stretch")

    baris_3t = df_3t.set_index("wilayah")
    pct_3t = baris_3t.loc["Wilayah 3T", "realisasi"] / baris_3t.loc["Wilayah 3T", "rencana"] * 100
    st.metric(
        "Kesesuaian Wilayah 3T",
        persen(pct_3t),
        help="Jumlah OJT yang ditempatkan di wilayah 3T dibagi rencana OJT wilayah tersebut.",
        icon=":material/location_on:",
    )

# ── Tab 2: Proyeksi Kekosongan 2027+ ─────────────────────────────────────────
with tab_proyeksi:
    st.subheader("Proyeksi Kekosongan Nasional")
    dasar_nasional = metrics.kekosongan_nasional_per_tahun()
    deret_kekosongan = sintetis.proyeksi_lanjutan(dasar_nasional)
    chart_deret = (
        alt.Chart(deret_kekosongan)
        .mark_line(point=True)
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            y=alt.Y("kekosongan:Q", title="Kekosongan"),
            color=alt.Color("sumber:N", title="Sumber Angka"),
            strokeDash=alt.StrokeDash("sumber:N", title="Sumber Angka"),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("kekosongan:Q", title="Kekosongan", format=","),
                alt.Tooltip("sumber:N", title="Sumber Angka"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart_deret, width="stretch")

    st.subheader("Perkiraan Kekosongan per Unit 2027")
    per_unit_dasar = metrics.kekosongan_per_unit(int(dasar_nasional["tahun"].max()))
    per_unit_dasar = per_unit_dasar.assign(
        perkiraan=(per_unit_dasar["kekosongan"] * sintetis.faktor_pertumbuhan(len(per_unit_dasar))).round()
    )
    chart_unit_2027 = (
        alt.Chart(per_unit_dasar)
        .mark_bar()
        .encode(
            x=alt.X("perkiraan:Q", title="Perkiraan Kekosongan"),
            y=alt.Y("nama_pendek:N", sort="-x", title="Unit Induk"),
            tooltip=[
                alt.Tooltip("nama_pendek:N", title="Unit Induk"),
                alt.Tooltip("perkiraan:Q", title="Perkiraan Kekosongan"),
            ],
        )
        .properties(height=max(320, 14 * len(per_unit_dasar)))
    )
    st.altair_chart(chart_unit_2027, width="stretch")

# ── Tab 3: Pencocokan Kompetensi ─────────────────────────────────────────────
with tab_kompetensi:
    st.subheader("Pencocokan Kompetensi Jabatan")
    df_kompetensi = sintetis.pencocokan_kompetensi()
    panjang_kompetensi = df_kompetensi.melt(
        id_vars="kompetensi",
        value_vars=["standar_jabatan", "capaian_pelamar"],
        var_name="jenis",
        value_name="nilai",
    )
    panjang_kompetensi["jenis"] = panjang_kompetensi["jenis"].map(
        {"standar_jabatan": "Standar Jabatan", "capaian_pelamar": "Capaian Pelamar"}
    )
    chart_kompetensi = (
        alt.Chart(panjang_kompetensi)
        .mark_bar()
        .encode(
            y=alt.Y("kompetensi:N", sort="-x", title="Dimensi Kompetensi"),
            x=alt.X("nilai:Q", title="Nilai"),
            xOffset=alt.XOffset("jenis:N", title="Jenis"),
            color=alt.Color("jenis:N", title="Jenis"),
            tooltip=[
                alt.Tooltip("kompetensi:N", title="Kompetensi"),
                alt.Tooltip("jenis:N", title="Jenis"),
                alt.Tooltip("nilai:Q", title="Nilai"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_kompetensi, width="stretch")

# ── Tab 4: Skor Tes & Ambang Kelulusan ───────────────────────────────────────
with tab_skor:
    st.subheader("Sebaran Skor Tes")
    df_skor, ambang = sintetis.sebaran_skor_tes()
    histogram_skor = (
        alt.Chart(df_skor)
        .mark_bar()
        .encode(
            x=alt.X("skor:Q", bin=alt.Bin(maxbins=30), title="Skor"),
            y=alt.Y("count():Q", title="Jumlah Peserta"),
        )
        .properties(height=280)
    )
    garis_ambang = (
        alt.Chart(pd.DataFrame({"ambang": [ambang]}))
        .mark_rule(color="#D13438", strokeDash=[6, 4])
        .encode(x=alt.X("ambang:Q", title="Ambang Kelulusan"))
    )
    st.altair_chart(histogram_skor + garis_ambang, width="stretch")

    proporsi_lulus = (df_skor["skor"] >= ambang).mean() * 100
    st.metric(
        "Proporsi Lulus Ambang",
        persen(proporsi_lulus),
        help="Persentase skor tes yang berada pada atau di atas ambang kelulusan.",
        icon=":material/check_circle:",
    )

# ── Tab 5: Peristiwa Karier per Orang ────────────────────────────────────────
with tab_karier:
    st.subheader("Peristiwa Karier per Tahun")
    df_karier = sintetis.peristiwa_karier()
    agregat_karier = df_karier.groupby(["tahun", "jenis"]).size().reset_index(name="jumlah")
    chart_karier = (
        alt.Chart(agregat_karier)
        .mark_bar()
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            y=alt.Y("jumlah:Q", title="Jumlah Peristiwa"),
            color=alt.Color("jenis:N", title="Jenis Peristiwa"),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("jenis:N", title="Jenis Peristiwa"),
                alt.Tooltip("jumlah:Q", title="Jumlah"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart_karier, width="stretch")

    st.dataframe(
        df_karier.sort_values(["tahun", "jenis"]).head(50),
        column_config={
            "id_pegawai": st.column_config.TextColumn("ID Pegawai"),
            "jenis": st.column_config.TextColumn("Jenis Peristiwa"),
            "tahun": st.column_config.NumberColumn("Tahun", format="%d"),
        },
        hide_index=True,
        width="stretch",
    )

# ── Tab 6: Efektivitas Sumber Rekrutmen ──────────────────────────────────────
with tab_sumber:
    st.subheader("Efektivitas Sumber Rekrutmen")
    df_sumber = sintetis.efektivitas_sumber_rekrutmen()
    kiri, kanan = st.columns(2)
    with kiri:
        st.markdown("**Volume Pelamar per Sumber**")
        chart_volume = (
            alt.Chart(df_sumber)
            .mark_bar()
            .encode(
                x=alt.X("jumlah_pelamar:Q", title="Jumlah Pelamar"),
                y=alt.Y("sumber:N", sort="-x", title="Sumber"),
                tooltip=[
                    alt.Tooltip("sumber:N", title="Sumber"),
                    alt.Tooltip("jumlah_pelamar:Q", title="Jumlah Pelamar", format=","),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(chart_volume, width="stretch")
    with kanan:
        st.markdown("**Konversi per Sumber**")
        chart_konversi = (
            alt.Chart(df_sumber)
            .mark_bar()
            .encode(
                x=alt.X("konversi_persen:Q", title="Konversi (%)"),
                y=alt.Y("sumber:N", sort="-x", title="Sumber"),
                tooltip=[
                    alt.Tooltip("sumber:N", title="Sumber"),
                    alt.Tooltip("konversi_persen:Q", title="Konversi (%)"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(chart_konversi, width="stretch")

# ── Tab 7: Lokasi SAMAPTA & Kapasitas UPDL ───────────────────────────────────
with tab_updl:
    st.subheader("Kapasitas SAMAPTA per UPDL")
    df_updl = sintetis.kapasitas_samapta_updl()
    panjang_updl = df_updl.melt(
        id_vars="updl", value_vars=["kapasitas", "terpakai"], var_name="jenis", value_name="jumlah"
    )
    panjang_updl["jenis"] = panjang_updl["jenis"].map({"kapasitas": "Kapasitas", "terpakai": "Terpakai"})
    chart_updl = (
        alt.Chart(panjang_updl)
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah Peserta"),
            y=alt.Y("updl:N", sort="-x", title="UPDL"),
            xOffset=alt.XOffset("jenis:N", title="Jenis"),
            color=alt.Color("jenis:N", title="Jenis"),
            tooltip=[
                alt.Tooltip("updl:N", title="UPDL"),
                alt.Tooltip("jenis:N", title="Jenis"),
                alt.Tooltip("jumlah:Q", title="Jumlah"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart_updl, width="stretch")

# ── Tab 8: Biaya Rekrutmen ───────────────────────────────────────────────────
with tab_biaya:
    st.subheader("Komponen Biaya Rekrutmen")
    df_biaya = sintetis.komponen_biaya_rekrutmen()
    chart_biaya = (
        alt.Chart(df_biaya)
        .mark_bar()
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            y=alt.Y("biaya_juta_rupiah:Q", title="Biaya (Juta Rupiah)"),
            color=alt.Color("komponen:N", title="Komponen"),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("komponen:N", title="Komponen"),
                alt.Tooltip("biaya_juta_rupiah:Q", title="Biaya (Juta Rupiah)", format=","),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_biaya, width="stretch")

    st.metric(
        "Biaya per Pegawai Diterima",
        f"Rp {angka(sintetis.biaya_per_pegawai_diterima())}",
        help="Total biaya rekrutmen dibagi jumlah pegawai yang diterima.",
        icon=":material/payments:",
    )
