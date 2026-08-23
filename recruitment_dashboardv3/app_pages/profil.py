"""Halaman 7 -- Profil Pelamar.

Pertanyaan harian: siapa yang melamar, dan cocok tidak dengan yang
dibutuhkan? Seperti Corong Seleksi (halaman 4) dan Rencana & Realisasi
(halaman 6), profil demografis pelamar 2019-2025 adalah riwayat yang sudah
tuntas dan tidak berubah lagi -- halaman ini tidak terikat `hari_ini()`
(penyimpangan yang sama, disetujui ATURAN_TAMPILAN.md §4.5).
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components.tampilan import keadaan_kosong
from core import metrics
from core.format import persen

_LABEL_GENDER = {"P": "Pria", "W": "Wanita"}

st.title("Profil Pelamar")

# ── Blok 1: piramida umur x jenis kelamin saat melamar ──────────────────────
st.subheader("Piramida Umur × Jenis Kelamin")
piramida = metrics.umur_gender_pelamar()

if piramida.empty:
    keadaan_kosong("Belum ada data pelamar")
else:
    piramida = piramida.assign(label_gender=piramida["jenis_kelamin"].map(_LABEL_GENDER))
    piramida["nilai"] = piramida["jumlah"].where(
        piramida["jenis_kelamin"] == "W", -piramida["jumlah"]
    )
    batas = int(piramida["jumlah"].max() * 1.1)
    tinggi_piramida = max(420, 20 * piramida["umur"].nunique())
    _chart_piramida = (
        alt.Chart(piramida)
        .mark_bar()
        .encode(
            y=alt.Y(
                "umur:O", sort=alt.SortField("umur", order="descending"), title="Umur saat melamar"
            ),
            x=alt.X(
                "nilai:Q",
                title="Jumlah pelamar",
                scale=alt.Scale(domain=[-batas, batas]),
                axis=alt.Axis(labelExpr="abs(datum.value)"),
            ),
            color=alt.Color(
                "label_gender:N", title="Jenis kelamin", legend=alt.Legend(orient="top")
            ),
            tooltip=[
                alt.Tooltip("umur:O", title="Umur"),
                alt.Tooltip("label_gender:N", title="Jenis Kelamin"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=tinggi_piramida)
    )
    st.altair_chart(_chart_piramida, width="stretch")

# ── Blok 2: jenjang pendidikan ───────────────────────────────────────────────
st.subheader("Jenjang Pendidikan Pelamar")
jenjang = metrics.jenjang_pendidikan_pelamar()

if jenjang.empty:
    keadaan_kosong("Belum ada data jenjang pendidikan")
else:
    _chart_jenjang = (
        alt.Chart(jenjang)
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah pelamar"),
            y=alt.Y("degree:N", sort="-x", title="Jenjang"),
            tooltip=[
                alt.Tooltip("degree:N", title="Jenjang"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=max(180, 45 * len(jenjang)))
    )
    st.altair_chart(_chart_jenjang, width="stretch")

# ── Blok 3: rumpun jurusan -- melamar vs diterima ────────────────────────────
st.subheader("Rumpun Jurusan: Melamar vs Diterima")
rumpun = metrics.rumpun_jurusan_konversi()

if rumpun.empty:
    keadaan_kosong("Belum ada data rumpun jurusan")
else:
    _chart_rumpun = (
        alt.Chart(rumpun)
        .mark_bar()
        .encode(
            x=alt.X("melamar:Q", title="Pelamar"),
            y=alt.Y("rumpun:N", sort="-x", title="Rumpun Jurusan"),
            tooltip=[
                alt.Tooltip("rumpun:N", title="Rumpun"),
                alt.Tooltip("melamar:Q", title="Melamar", format=","),
                alt.Tooltip("diterima:Q", title="Diterima", format=","),
            ],
        )
        .properties(height=max(360, 24 * len(rumpun)))
    )
    st.altair_chart(_chart_rumpun, width="stretch")

    rumpun_tampil = rumpun.assign(
        pct_konversi=(100.0 * rumpun["diterima"] / rumpun["melamar"]).round(1)
    )
    st.dataframe(
        rumpun_tampil,
        column_config={
            "rumpun": "Rumpun Jurusan",
            "melamar": st.column_config.NumberColumn("Melamar", format="localized"),
            "diterima": st.column_config.NumberColumn("Diterima", format="localized"),
            "pct_konversi": st.column_config.NumberColumn("Konversi (%)", format="%.1f%%"),
        },
        hide_index=True,
        width="stretch",
    )

# ── Blok 4: sebaran provinsi domisili ────────────────────────────────────────
st.subheader("Sebaran Provinsi Domisili")
provinsi = metrics.provinsi_domisili_pelamar()

if provinsi.empty:
    keadaan_kosong("Belum ada data provinsi domisili")
else:
    provinsi_tampil = provinsi.assign(
        label_provinsi=provinsi["propinsi_domisili"].fillna("Tidak Diketahui")
    )
    _chart_provinsi = (
        alt.Chart(provinsi_tampil)
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah pelamar"),
            y=alt.Y("label_provinsi:N", sort="-x", title="Provinsi"),
            tooltip=[
                alt.Tooltip("label_provinsi:N", title="Provinsi"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=max(420, 20 * len(provinsi_tampil)))
    )
    st.altair_chart(_chart_provinsi, width="stretch")

# ── Blok 5: volume tes per kota ──────────────────────────────────────────────
st.subheader("Volume Tes per Kota")
kota = metrics.volume_tes_per_kota()

if kota.empty:
    keadaan_kosong("Belum ada data tes tatap muka")
else:
    _chart_kota = (
        alt.Chart(kota)
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah sesi tes"),
            y=alt.Y("lokasi_kota:N", sort="-x", title="Kota"),
            tooltip=[
                alt.Tooltip("lokasi_kota:N", title="Kota"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=max(500, 14 * len(kota)))
    )
    st.altair_chart(_chart_kota, width="stretch")

# ── Blok 6: kelengkapan akun per kohort ──────────────────────────────────────
st.subheader("Kelengkapan Akun per Kohort")
kohort = metrics.kelengkapan_akun_per_kohort()

if kohort.empty:
    keadaan_kosong("Belum ada data kohort pelamar")
else:
    baris_terbaru = kohort.sort_values("tahun_kohort").iloc[-1]
    with st.container(border=True, horizontal=True):
        st.metric(
            "Kelengkapan Kohort Terbaru",
            persen(baris_terbaru["pct_lengkap"]),
            help="Akun dengan surel teraktivasi dan alamat domisili terisi, kohort tahun terbaru.",
            icon=":material/verified_user:",
        )
    _chart_kohort = (
        alt.Chart(kohort)
        .mark_line(point=True)
        .encode(
            x=alt.X("tahun_kohort:O", title="Tahun kohort"),
            y=alt.Y("pct_lengkap:Q", title="Kelengkapan (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=[
                alt.Tooltip("tahun_kohort:O", title="Tahun Kohort"),
                alt.Tooltip("total:Q", title="Total Kandidat", format=","),
                alt.Tooltip("lengkap:Q", title="Lengkap & Aktif", format=","),
                alt.Tooltip("pct_lengkap:Q", title="Kelengkapan (%)"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(_chart_kohort, width="stretch")
