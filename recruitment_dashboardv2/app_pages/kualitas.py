"""Halaman 7 — Kualitas Data & Sumber Sistem.

Pertanyaan yang dijawab: mana yang kita punya, mana yang masih perlu dikumpulkan?
Satu-satunya halaman yang boleh melebihi 4 blok (D5) — isinya katalog teknis
tentang dashboard ini sendiri, bukan analisis bisnis berlapis. Tidak punya lapis
analis. Lihat docs/wireframe.md Halaman 7.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Kualitas Data & Sumber Sistem")

sistem = metrics.volume_per_sistem().set_index("sistem_sumber")["n"]
kelengkapan = metrics.kelengkapan_per_kohort()
selisih = metrics.selisih_angka_rencana()
rbb = metrics.jejak_rbb()

rekrutmen_n = int(sistem.get("rekrutmen.pln.co.id", 0))
seleksi_n = int(sistem.get("seleksi.pln.co.id", 0))
upload_n = int(sistem.get("rekrutmen.pln.co.id (hasil di-upload)", 0))
pct_terlihat = rbb.iloc[-1]["pct_terlihat"]

# ── Blok jangkar: alur 4 sistem ─────────────────────────────────────────────
with ui.temuan_halaman(
    "Empat sistem, satu perjalanan orang — tidak satu pun bisa berdiri sendiri "
    "menjawab \"berapa orang sedang OJT\""
):
    node = st.columns([3, 1, 3, 1, 3, 1, 2, 1, 2])
    isi_node = [
        ("FHCI", f"agregat, {persen(pct_terlihat, 2)} terlihat"),
        None,
        ("rekrutmen.pln.co.id", f"{angka(rekrutmen_n)} baris"),
        None,
        ("seleksi.pln.co.id", f"{angka(seleksi_n)} baris · +{angka(upload_n)} upload vendor"),
        None,
        ("Pusdiklat", "titik rawan integrasi"),
        None,
        ("HTD", "SK & data pegawai"),
    ]
    for kol, item in zip(node, isi_node):
        with kol:
            if item is None:
                st.write("")
                st.markdown(":material/arrow_forward:")
            else:
                nama, sub = item
                with st.container(border=True, height=100):
                    st.markdown(f"**{nama}**")
                    st.caption(sub)

# ── Dua blok pendukung (maks 2 di halaman biasa; halaman ini dikecualikan D5) ─
kiri, kanan = st.columns(2)

with kiri:
    kelengkapan_plot = kelengkapan.melt(
        id_vars=["kualitas_kohort"], value_vars=["pct_blok_fisik", "pct_domisili"],
        var_name="kolom", value_name="pct",
    )
    kelengkapan_plot["kolom"] = kelengkapan_plot["kolom"].map(
        {"pct_blok_fisik": "Blok fisik", "pct_domisili": "Domisili"}
    )
    with ui.blok_chart("Kelengkapan data membaik tiap tahap kualitas kohort"):
        st.altair_chart(
            alt.Chart(kelengkapan_plot)
            .mark_rect()
            .encode(
                y=alt.Y("kualitas_kohort:N", sort=["RENDAH", "SEDANG", "BAIK"], title=None),
                x=alt.X("kolom:N", title=None),
                color=alt.Color("pct:Q", scale=alt.Scale(scheme="blues"), title="Persen lengkap"),
                tooltip=[
                    alt.Tooltip("kualitas_kohort:N", title="Kualitas kohort"),
                    alt.Tooltip("kolom:N", title="Kolom"),
                    alt.Tooltip("pct:Q", title="Lengkap", format=".1f"),
                ],
            )
            .properties(height=220)
        )

with kanan:
    with ui.blok_chart(
        f"Dua angka rencana tak pernah didamaikan, selisih melebar ke {angka(selisih.iloc[-1]['selisih'])}"
    ):
        st.altair_chart(
            alt.Chart(selisih)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=theme.warna_seri(0))
            .encode(
                x=alt.X("tahun:O", title=None),
                y=alt.Y("selisih:Q", title=None),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("target_gelombang:Q", title="Target gelombang", format=","),
                    alt.Tooltip("pagu:Q", title="Pagu disetujui", format=","),
                    alt.Tooltip("selisih:Q", title="Selisih", format=","),
                ],
            )
            .properties(height=220)
        )

# ── Referensi teknis: bukan chart, tabel katalog (bukan pelanggaran D5) ─────
with st.container(border=True):
    st.markdown("**Kolom dimodelkan & anomali yang diketahui**")
    referensi = pd.DataFrame(
        [
            {"Hal": "Kuota per posisi", "Keterangan": "Domain HST, tidak ada di HTD", "Rujukan": "F-017"},
            {"Hal": "Passing grade", "Keterangan": "Tidak ada di Perdir 0056/0050/0048", "Rujukan": "F-028"},
            {"Hal": "Skor tes mentah", "Keterangan": "Sistem asli hanya simpan lulus/gagal", "Rujukan": "F-017"},
            {
                "Hal": "UID Jawa Tengah & DIY",
                "Keterangan": "jumlah_pegawai=4 vs ftk_2025=144 — gagal match DAPEG",
                "Rujukan": "ISSUES_MASTER_DATA.md",
            },
            {
                "Hal": "realisasi_apr_2026",
                "Keterangan": "Hanya terisi 1 dari 48 unit — semua gap pakai Mar-2026",
                "Rujukan": "M13",
            },
            {
                "Hal": "5 kolom kandidat",
                "Keterangan": "Dibagikan acak seragam (kota_domisili, kota_asal, sekolah_universitas, dll)",
                "Rujukan": "ISSUES_SEBARAN.md",
            },
        ]
    )
    st.dataframe(referensi, hide_index=True, width="stretch")

ui.tentang_halaman(
    "Halaman ini tidak punya lapis analis — isinya sudah sepenuhnya level teknis, "
    "bukan analisis bisnis berlapis seperti 6 halaman lainnya.\n\n"
    "**Jalur RBB** hanya berjejak {pct}% di sistem PLN — FHCI menyaring jutaan "
    "pelamar sebelum kandidat terpilih masuk `rekrutmen.pln.co.id`, jadi 218.928 "
    "pendaftaran di halaman lain BUKAN representasi total pasar kerja BUMN.".format(
        pct=persen(pct_terlihat, 2)
    )
)
