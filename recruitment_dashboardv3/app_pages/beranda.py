"""Halaman 1 -- Beranda.

Pertanyaan harian: apa yang perlu perhatian hari ini? Seluruh isi halaman
dihitung ulang terhadap `core.db.hari_ini()` -- lihat docs/RANCANGAN_HALAMAN.md
§3. Tidak ada teks di sini yang di-hardcode terhadap satu tanggal tertentu;
isinya berubah sendiri seiring hari maju.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components.tampilan import keadaan_kosong
from core import metrics
from core.format import angka

HARI_TENGGAT = 30

st.title("Beranda")

keadaan = metrics.keadaan_sekarang()
tenggat = metrics.tenggat_terdekat(hari=HARI_TENGGAT)
pipeline = metrics.denyut_pipeline().sort_values("urutan")
aktivitas = metrics.aktivitas_sekitar()

# ── Kartu keadaan sekarang ───────────────────────────────────────────────────
st.subheader("Keadaan Sekarang")
with st.container(border=True, horizontal=True):
    st.metric(
        "Gelombang Dibuka",
        angka(keadaan["gelombang_dibuka"]),
        help="Gelombang yang pendaftarannya sedang berlangsung.",
        icon=":material/campaign:",
    )
    st.metric(
        "Sedang Diseleksi",
        angka(keadaan["sedang_diseleksi"]),
        help="Pelamar yang sudah menjalani salah satu tahap seleksi, belum gugur, dan hasil akhirnya belum diumumkan.",
        icon=":material/fact_check:",
    )
    st.metric(
        "Sedang OJT",
        angka(keadaan["sedang_ojt"]),
        help="Peserta yang sedang menjalani diklat prajabatan.",
        icon=":material/school:",
    )
    st.metric(
        "Menunggu SK",
        angka(keadaan["menunggu_sk"]),
        help="Peserta yang sudah selesai diklat prajabatan, SK pengangkatannya belum terbit.",
        icon=":material/description:",
    )

# ── Tenggat terdekat ─────────────────────────────────────────────────────────
st.subheader(
    "Tenggat Terdekat",
    help=f"Peristiwa yang jatuh tempo dalam {HARI_TENGGAT} hari ke depan, diurutkan dari yang paling dekat.",
)
if tenggat.empty:
    keadaan_kosong(f"Tidak ada tenggat dalam {HARI_TENGGAT} hari ke depan")
else:
    st.dataframe(
        tenggat.rename(columns={"jenis": "peristiwa"}),
        column_order=["tanggal", "hari_tersisa", "peristiwa", "tahap", "jumlah"],
        column_config={
            "tanggal": st.column_config.DateColumn("Tanggal", format="D MMM YYYY"),
            "hari_tersisa": st.column_config.NumberColumn("Hari Lagi"),
            "peristiwa": st.column_config.TextColumn("Peristiwa"),
            "tahap": st.column_config.TextColumn("Tahap"),
            "jumlah": st.column_config.NumberColumn("Jumlah", format="localized"),
        },
        hide_index=True,
        width="stretch",
    )

# ── Denyut pipeline ──────────────────────────────────────────────────────────
st.subheader(
    "Denyut Pipeline Seleksi",
    help="Jumlah orang yang saat ini berada di tiap tahap, dari Pendaftaran sampai SK Pengangkatan.",
)
_primer = st.context.theme.get("primaryColor") or "#0078D4"
_funnel = go.Figure(
    go.Funnel(
        y=pipeline["nama"],
        x=pipeline["jumlah"],
        textposition="inside",
        textinfo="value",
        marker=dict(color=_primer),
        customdata=pipeline[["sedang_berjalan", "sudah_tuntas"]].to_numpy(),
        hovertemplate=(
            "%{y}<br>Jumlah: %{x:,}<br>"
            "Sedang berjalan: %{customdata[0]:,}<br>"
            "Sudah tuntas: %{customdata[1]:,}<extra></extra>"
        ),
    )
)
_funnel.update_layout(
    margin=dict(l=0, r=0, t=10, b=10),
    height=420,
    font=dict(family="Segoe UI, Open Sans, sans-serif"),
)
st.plotly_chart(_funnel, width="stretch", config={"displayModeBar": False})

# ── Aktivitas terakhir & berikutnya ──────────────────────────────────────────
st.subheader("Aktivitas Terakhir & Berikutnya")
_terakhir = aktivitas[aktivitas["arah"] == "terakhir"]
_berikutnya = aktivitas[aktivitas["arah"] == "berikutnya"]

kiri, kanan = st.columns(2)

with kiri:
    st.markdown("**Terakhir**")
    if _terakhir.empty:
        keadaan_kosong("Tidak ada aktivitas terakhir yang tercatat")
    else:
        baris = _terakhir.iloc[0]
        with st.container(border=True):
            st.metric(
                baris["tahap"],
                angka(baris["jumlah"]),
                help="Peristiwa terakhir yang sudah terjadi sebelum tanggal acuan.",
                icon=":material/history:",
            )
            st.markdown(f":gray[{baris['jenis']} · {abs(int(baris['selisih_hari']))} hari lalu]")

with kanan:
    st.markdown("**Berikutnya**")
    if _berikutnya.empty:
        keadaan_kosong("Tidak ada aktivitas berikutnya yang terjadwal")
    else:
        baris = _berikutnya.iloc[0]
        with st.container(border=True):
            st.metric(
                baris["tahap"],
                angka(baris["jumlah"]),
                help="Peristiwa terjadwal berikutnya sesudah tanggal acuan.",
                icon=":material/upcoming:",
            )
            st.markdown(f":gray[{baris['jenis']} · {int(baris['selisih_hari'])} hari lagi]")
