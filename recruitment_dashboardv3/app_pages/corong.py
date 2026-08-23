"""Halaman 4 -- Corong Seleksi.

Pertanyaan harian: di tahap mana orang hilang, dan kenapa? Berbeda dari
Seleksi Berjalan (halaman 3), yang membaca satu gelombang yang sedang jalan --
di sini analisisnya lintas gelombang, atas riwayat yang sudah tuntas. Karena
itu halaman ini tidak terikat `hari_ini()`: nilai analitisnya historis, bukan
snapshot hari ini, dan tidak pernah kosong -- data seleksi 2019-2025 sudah
final.
"""

from __future__ import annotations

import altair as alt
import plotly.graph_objects as go
import streamlit as st

from components.tampilan import keadaan_kosong
from core import metrics
from core.format import angka

_LABEL_TAHAP = {
    "administrasi": "Administrasi",
    "adaptif": "Adaptif",
    "akademik_inggris": "Akademik & Inggris",
    "psikologi": "Psikologi",
    "fisik_mcu": "Fisik & MCU",
    "wawancara": "Wawancara",
}
_URUTAN_TAHAP = list(_LABEL_TAHAP)

_LABEL_FHCI = {
    "fhci_administrasi": "Administrasi (FHCI)",
    "fhci_tes_online_1": "Tes Online 1",
    "fhci_tes_online_2": "Tes Online 2",
}

_LABEL_MODE = {"online": "Online", "offline": "Offline", "dokumen": "Dokumen"}


def _bangun_sankey(df, rbb_masuk: int) -> go.Figure:
    """Corong enam tahap sebagai Sankey, memisahkan gugur tes dari tidak hadir.

    Setiap tahap punya node masuk & lulus sendiri; cabang gugur (merah) dan
    tidak hadir (kuning) dipisah -- Seleksi Administrasi tidak punya cabang
    tidak hadir karena berbasis dokumen. Titik serah-terima RBB digambar
    sebagai node masuk tersendiri yang menyatu ke node masuk Akademik &
    Inggris, bukan angka terputus.
    """
    d = df.set_index("tahap_kode")
    warna_primer = st.context.theme.get("primaryColor") or "#0078D4"
    warna_netral = st.context.theme.get("secondaryBackgroundColor") or "#D3D3D3"
    warna_gugur = "#D13438"
    warna_tidak_hadir = "#FFB900"
    warna_rbb = "#8764B8"

    urutan_node: list[str] = []
    warna_node: list[str] = []
    nilai_node: dict[str, int] = {}
    indeks_node: dict[str, int] = {}
    sumber: list[int] = []
    tujuan: list[int] = []
    nilai_tautan: list[int] = []
    warna_tautan: list[str] = []

    def daftarkan(label: str, nilai: int, warna: str) -> None:
        if label not in indeks_node:
            indeks_node[label] = len(urutan_node)
            urutan_node.append(label)
            warna_node.append(warna)
        nilai_node[label] = nilai

    def tautkan(asal: str, akhir: str, nilai: int, warna: str) -> None:
        if nilai <= 0:
            return
        sumber.append(indeks_node[asal])
        tujuan.append(indeks_node[akhir])
        nilai_tautan.append(nilai)
        warna_tautan.append(warna)

    lulus_sebelumnya: str | None = None
    nilai_lulus_sebelumnya = 0
    for i, kode in enumerate(_URUTAN_TAHAP):
        baris = d.loc[kode]
        pendek = _LABEL_TAHAP[kode]
        label_masuk = "Pendaftaran" if i == 0 else f"Masuk {pendek}"
        label_lulus = "Diterima" if i == len(_URUTAN_TAHAP) - 1 else f"Lulus {pendek}"
        label_gugur = f"Gugur {pendek}"
        label_tdk_hadir = f"Tidak Hadir {pendek}"

        gugur_tes = int(baris["gagal"]) - int(baris["tidak_hadir"])
        tidak_hadir_v = int(baris["tidak_hadir"])

        daftarkan(label_masuk, int(baris["masuk"]), warna_netral)
        daftarkan(label_lulus, int(baris["lulus"]), warna_primer)
        if gugur_tes > 0:
            daftarkan(label_gugur, gugur_tes, warna_gugur)
        if tidak_hadir_v > 0:
            daftarkan(label_tdk_hadir, tidak_hadir_v, warna_tidak_hadir)

        if lulus_sebelumnya is not None:
            tautkan(lulus_sebelumnya, label_masuk, nilai_lulus_sebelumnya, warna_primer)
        if kode == "akademik_inggris" and rbb_masuk > 0:
            daftarkan("Masuk RBB", rbb_masuk, warna_rbb)
            tautkan("Masuk RBB", label_masuk, rbb_masuk, warna_rbb)

        tautkan(label_masuk, label_lulus, int(baris["lulus"]), warna_primer)
        if gugur_tes > 0:
            tautkan(label_masuk, label_gugur, gugur_tes, warna_gugur)
        if tidak_hadir_v > 0:
            tautkan(label_masuk, label_tdk_hadir, tidak_hadir_v, warna_tidak_hadir)

        lulus_sebelumnya = label_lulus
        nilai_lulus_sebelumnya = int(baris["lulus"])

    label_tampil = [f"{nama}<br>{angka(nilai_node[nama])}" for nama in urutan_node]
    fig = go.Figure(
        go.Sankey(
            node=dict(
                label=label_tampil,
                color=warna_node,
                pad=18,
                thickness=16,
                line=dict(width=0),
            ),
            link=dict(source=sumber, target=tujuan, value=nilai_tautan, color=warna_tautan),
            textfont=dict(size=12),
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=10),
        font=dict(family="Segoe UI, Open Sans, sans-serif"),
    )
    return fig


st.title("Corong Seleksi")

# ── Blok 1: corong enam tahap jalur mandiri ─────────────────────────────────
st.subheader("Corong Jalur Mandiri")
corong = metrics.corong_tahap_seleksi()
rbb_nasional = metrics.rbb_masuk_akademik_inggris()
sankey_nasional = _bangun_sankey(corong, rbb_nasional)
sankey_nasional.update_layout(height=520)
st.plotly_chart(sankey_nasional, width="stretch", config={"displayModeBar": False})

# ── Blok 2: no-show per tahap x mode ─────────────────────────────────────────
st.subheader("No-show per Tahap × Mode")
no_show = metrics.no_show_per_tahap_mode()
no_show = no_show.assign(
    label_mode=no_show["mode"].map(_LABEL_MODE),
)
_chart_no_show = (
    alt.Chart(no_show)
    .mark_bar()
    .encode(
        x=alt.X("pct_no_show:Q", title="No-show (%)"),
        y=alt.Y("nama:N", sort=alt.SortField("urutan"), title="Tahap"),
        color=alt.Color("label_mode:N", title="Mode"),
        tooltip=[
            alt.Tooltip("nama:N", title="Tahap"),
            alt.Tooltip("label_mode:N", title="Mode"),
            alt.Tooltip("pct_no_show:Q", title="No-show (%)"),
            alt.Tooltip("tidak_hadir:Q", title="Jumlah No-show", format=","),
        ],
    )
    .properties(height=260)
)
st.altair_chart(_chart_no_show, width="stretch")

# ── Blok 3: titik serah-terima RBB ──────────────────────────────────────────
st.subheader("Titik Serah-Terima RBB")
_lulus_adaptif = int(corong.set_index("tahap_kode").loc["adaptif", "lulus"])
_masuk_akademik = int(corong.set_index("tahap_kode").loc["akademik_inggris", "masuk"])
with st.container(border=True, horizontal=True):
    st.metric(
        "Lulus Adaptif",
        angka(_lulus_adaptif),
        help="Pelamar jalur mandiri yang lolos Tes Adaptif PLN.",
        icon=":material/check_circle:",
    )
    st.metric(
        "Masuk RBB",
        angka(rbb_nasional),
        help="Pelamar yang diserahkan dari FHCI langsung ke tahap Akademik & Inggris, tanpa melalui Seleksi Administrasi maupun Tes Adaptif PLN.",
        icon=":material/swap_horiz:",
    )
    st.metric(
        "Masuk Akademik & Inggris",
        angka(_masuk_akademik),
        help="Total pelamar yang memasuki tahap Akademik & Inggris, dari kedua jalur.",
        icon=":material/login:",
    )

# ── Blok 4: corong FHCI terpisah ────────────────────────────────────────────
st.subheader("Corong FHCI")
fhci = metrics.corong_fhci()
_label_fhci = [_LABEL_FHCI[k] for k in fhci["tahap_kode"]] + ["Lulus FHCI"]
_nilai_fhci = list(fhci["masuk"]) + [int(fhci["lulus"].iloc[-1])]
_warna_primer = st.context.theme.get("primaryColor") or "#0078D4"
_funnel_fhci = go.Figure(
    go.Funnel(
        y=_label_fhci,
        x=_nilai_fhci,
        textposition="inside",
        textinfo="value",
        marker=dict(color=_warna_primer),
    )
)
_funnel_fhci.update_layout(
    margin=dict(l=0, r=0, t=10, b=10),
    height=320,
    font=dict(family="Segoe UI, Open Sans, sans-serif"),
)
st.plotly_chart(_funnel_fhci, width="stretch", config={"displayModeBar": False})

# ── Blok 5: pembanding antar gelombang ──────────────────────────────────────
st.subheader("Pembanding Antar Gelombang")
daftar = metrics.daftar_gelombang()
_opsi = daftar["gelombang_id"].tolist()
_nama_per_id = daftar.set_index("gelombang_id")["nama_gelombang"]

kiri, kanan = st.columns(2)
with kiri:
    gelombang_a = st.selectbox(
        "Gelombang A",
        options=_opsi,
        index=0,
        format_func=lambda kode: _nama_per_id.loc[kode],
        key="corong_gelombang_a",
    )
    corong_a = metrics.corong_tahap_seleksi(gelombang_a)
    if corong_a.empty:
        keadaan_kosong("Gelombang ini tidak punya data seleksi")
    else:
        rbb_a = metrics.rbb_masuk_akademik_inggris(gelombang_a)
        sankey_a = _bangun_sankey(corong_a, rbb_a)
        sankey_a.update_layout(height=420)
        st.plotly_chart(sankey_a, width="stretch", config={"displayModeBar": False})

with kanan:
    gelombang_b = st.selectbox(
        "Gelombang B",
        options=_opsi,
        index=min(1, len(_opsi) - 1),
        format_func=lambda kode: _nama_per_id.loc[kode],
        key="corong_gelombang_b",
    )
    corong_b = metrics.corong_tahap_seleksi(gelombang_b)
    if corong_b.empty:
        keadaan_kosong("Gelombang ini tidak punya data seleksi")
    else:
        rbb_b = metrics.rbb_masuk_akademik_inggris(gelombang_b)
        sankey_b = _bangun_sankey(corong_b, rbb_b)
        sankey_b.update_layout(height=420)
        st.plotly_chart(sankey_b, width="stretch", config={"displayModeBar": False})
