"""Halaman 5 -- Pasca-Seleksi.

Pertanyaan harian: yang sudah lulus, sekarang prosesnya di mana? Berbeda dari
Corong Seleksi (halaman 4), yang historis dan tuntas: di sini "posisi hari ini"
adalah penanda yang bergerak seiring tanggal, jadi halaman ini terikat penuh ke
`db.hari_ini()` -- sama seperti Beranda dan Seleksi Berjalan, bukan dikecualikan
seperti Corong Seleksi (ATURAN_TAMPILAN.md §4.5).
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from components.tampilan import keadaan_kosong
from core import db, metrics
from core.format import angka

st.title("Pasca-Seleksi")

acuan = db.hari_ini()

daftar_kohort = metrics.daftar_kohort_pasca()
if daftar_kohort.empty:
    keadaan_kosong("Belum ada kohort yang memasuki pasca-seleksi")
    st.stop()

_opsi_kohort = daftar_kohort["gelombang_id"].tolist()
_nama_per_kohort = daftar_kohort.set_index("gelombang_id")["nama_gelombang"]
_default = metrics.kohort_relevan(acuan)
_indeks_default = _opsi_kohort.index(_default) if _default in _opsi_kohort else 0

gelombang_id = st.selectbox(
    "Kohort",
    options=_opsi_kohort,
    index=_indeks_default,
    format_func=lambda kode: f"{_nama_per_kohort.loc[kode]} ({kode})",
)

# ── Blok 1: lini masa tujuh tahap ────────────────────────────────────────────
st.subheader("Lini Masa Pasca-Seleksi")
lini_masa = metrics.lini_masa_pasca_kohort(gelombang_id, acuan=acuan)

_ada_jadwal = lini_masa["tanggal_mulai"].notna()
_gantt = lini_masa[_ada_jadwal].copy()


def _status_dominan(baris: pd.Series) -> str:
    if baris["peserta"] == 0:
        return "Belum ada data"
    if baris["selesai"] == baris["peserta"]:
        return "Selesai"
    if baris["belum_mulai"] == baris["peserta"]:
        return "Menunggu Mulai"
    return "Berjalan"


if _gantt.empty:
    keadaan_kosong("Kohort ini belum punya jadwal pasca-seleksi")
else:
    _gantt["status_tahap"] = _gantt.apply(_status_dominan, axis=1)
    _warna_primer = st.context.theme.get("primaryColor") or "#0078D4"
    _warna_netral = st.context.theme.get("secondaryBackgroundColor") or "#D3D3D3"
    _chart_lini_masa = (
        alt.Chart(_gantt)
        .mark_bar(height=18)
        .encode(
            x=alt.X("tanggal_mulai:T", title="Tanggal"),
            x2="tanggal_selesai:T",
            y=alt.Y("nama:N", sort=alt.SortField("urutan"), title="Tahap"),
            color=alt.Color(
                "status_tahap:N",
                title="Status",
                scale=alt.Scale(
                    domain=["Selesai", "Berjalan", "Menunggu Mulai"],
                    range=[_warna_primer, "#FFB900", _warna_netral],
                ),
            ),
            tooltip=[
                alt.Tooltip("nama:N", title="Tahap"),
                alt.Tooltip("tanggal_mulai:T", title="Mulai", format="%d %b %Y"),
                alt.Tooltip("tanggal_selesai:T", title="Selesai", format="%d %b %Y"),
                alt.Tooltip("peserta:Q", title="Peserta"),
                alt.Tooltip("selesai:Q", title="Sudah Selesai"),
                alt.Tooltip("berjalan:Q", title="Sedang Berjalan"),
                alt.Tooltip("belum_mulai:Q", title="Menunggu Mulai"),
            ],
        )
        .properties(height=max(220, 32 * len(_gantt)))
    )
    _rule_hari_ini = (
        alt.Chart(pd.DataFrame({"acuan": [pd.Timestamp(acuan)]}))
        .mark_rule(color="#D13438", strokeDash=[4, 4])
        .encode(x="acuan:T")
    )
    st.altair_chart(_chart_lini_masa + _rule_hari_ini, width="stretch")

st.markdown("**Rincian per Tahap**")
st.dataframe(
    lini_masa,
    column_order=["nama", "peserta", "tanggal_mulai", "tanggal_selesai", "selesai", "berjalan", "belum_mulai"],
    column_config={
        "nama": st.column_config.TextColumn("Tahap"),
        "peserta": st.column_config.NumberColumn("Peserta", format="localized"),
        "tanggal_mulai": st.column_config.DateColumn("Mulai", format="D MMM YYYY"),
        "tanggal_selesai": st.column_config.DateColumn("Selesai", format="D MMM YYYY"),
        "selesai": st.column_config.NumberColumn("Sudah Selesai", format="localized"),
        "berjalan": st.column_config.NumberColumn("Sedang Berjalan", format="localized"),
        "belum_mulai": st.column_config.NumberColumn("Menunggu Mulai", format="localized"),
    },
    hide_index=True,
    width="stretch",
)

# ── Blok 2: SAMAPTA ──────────────────────────────────────────────────────────
st.subheader("SAMAPTA")
samapta = metrics.status_samapta_kohort(gelombang_id)
if samapta is None:
    keadaan_kosong("Kohort ini belum menjalani SAMAPTA")
else:
    with st.container(border=True, horizontal=True):
        st.metric(
            "Peserta",
            angka(samapta["peserta"]),
            help="Peserta yang menjalani tahap SAMAPTA pada kohort ini.",
            icon=":material/fitness_center:",
        )
        st.metric(
            "Jendela Pelaksanaan",
            f"{samapta['tanggal_mulai']:%d %b} – {samapta['tanggal_selesai']:%d %b %Y}",
            icon=":material/date_range:",
        )
        st.metric(
            "Durasi",
            f"{angka(samapta['durasi_hari'])} hari",
            icon=":material/hourglass_top:",
        )

# ── Blok 3: Pembidangan ──────────────────────────────────────────────────────
st.subheader("Pembidangan Kohort")
pembidangan = metrics.pembidangan_per_kohort(gelombang_id)
if pembidangan.empty:
    keadaan_kosong("Kohort ini belum memasuki pembidangan")
else:
    _chart_pembidangan = (
        alt.Chart(pembidangan)
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah Peserta"),
            y=alt.Y("bidang_pembidangan:N", sort="-x", title="Bidang"),
            tooltip=[
                alt.Tooltip("bidang_pembidangan:N", title="Bidang"),
                alt.Tooltip("jumlah:Q", title="Jumlah"),
            ],
        )
        .properties(height=max(220, 32 * len(pembidangan)))
    )
    st.altair_chart(_chart_pembidangan, width="stretch")

# ── Blok 4: OJT per UPDL ─────────────────────────────────────────────────────
st.subheader("OJT per UPDL")
ojt_updl = metrics.ojt_per_updl_kohort(gelombang_id)
if ojt_updl["jumlah"].sum() == 0:
    keadaan_kosong("Kohort ini belum memasuki OJT")
else:
    _chart_ojt = (
        alt.Chart(ojt_updl)
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah Peserta"),
            y=alt.Y("nama_updl:N", sort="-x", title="UPDL"),
            tooltip=[
                alt.Tooltip("nama_updl:N", title="UPDL"),
                alt.Tooltip("jumlah:Q", title="Jumlah"),
            ],
        )
        .properties(height=max(220, 32 * len(ojt_updl)))
    )
    st.altair_chart(_chart_ojt, width="stretch")

# ── Blok 5: SK penempatan ────────────────────────────────────────────────────
st.subheader("SK Penempatan")
status_sk = metrics.status_sk_kohort(gelombang_id, acuan=acuan)
with st.container(border=True, horizontal=True):
    st.metric(
        "Sudah Terbit",
        angka(status_sk["terbit"]),
        help="Peserta yang SK pengangkatan & penempatannya sudah terbit.",
        icon=":material/task_alt:",
    )
    st.metric(
        "Menunggu",
        angka(status_sk["menunggu"]),
        help="Peserta yang SK pengangkatan & penempatannya belum terbit.",
        icon=":material/schedule:",
    )

unit_tujuan = metrics.unit_tujuan_sk_kohort(gelombang_id)
st.markdown("**Unit Tujuan Penempatan**")
if unit_tujuan.empty:
    keadaan_kosong("Unit tujuan belum ditetapkan")
else:
    st.dataframe(
        unit_tujuan,
        column_config={
            "nama_pendek": st.column_config.TextColumn("Unit"),
            "jumlah": st.column_config.NumberColumn("Jumlah", format="localized"),
        },
        hide_index=True,
        width="stretch",
        height=320,
    )
