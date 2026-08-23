"""Dua helper tampilan v3 -- keduanya bukan primitif tata letak.

`recruitment_dashboardv2/components/ui.py` dibuang seluruhnya (lihat
`docs/ATURAN_TAMPILAN.md` §1). Hanya dua fungsi yang boleh ada di sini --
jangan menambah yang ketiga tanpa membicarakannya lebih dulu.
"""

from __future__ import annotations

import streamlit as st

IKON_KOSONG_DEFAULT = ":material/inbox:"


def tinggi_kontainer(key: str, offset_px: int) -> None:
    """Batasi tinggi kontainer berkunci `key` supaya isi sampai mentok bawah (P8).

    Menyuntik CSS lewat selektor `.st-key-<key>` -- satu-satunya selektor
    kontainer yang didukung resmi Streamlit; selektor internal lain (mis.
    `[data-testid=...]`) berubah tanpa pemberitahuan antar versi dan tidak
    boleh dipakai. Panggil ini sesudah kontainer berkunci `key` dibuat.

    Ini pengganti `st.container(height=420)` -- tinggi piksel tetap memotong
    isi di tengah pada layar yang lebih pendek, dan menyisakan ruang kosong
    pada layar yang lebih tinggi.
    """
    st.html(
        f"""
        <style>
        .st-key-{key} {{
            max-height: calc(100vh - {offset_px}px);
            overflow-y: auto;
        }}
        </style>
        """
    )


def keadaan_kosong(keadaan: str, ikon: str | None = None, terakhir: str | None = None) -> None:
    """Keadaan kosong yang bermartabat (ATURAN_TAMPILAN.md §4.3).

    `keadaan` adalah frasa benda atau pernyataan keadaan pendek -- fakta
    keadaan apa adanya. Bentuk negatif sah ("Tidak ada gelombang yang sedang
    dibuka"). Yang dilarang: menerangkan sebab kosongnya (itu P2, tulis di
    `docs/CATATAN_DATA.md`). `terakhir` -- kalau diisi -- hanya penunjuk
    pendek ke hal terakhir yang selesai, bukan kalimat penjelas.

    PERINGATAN -- fungsi ini berisiko jadi `temuan_halaman()` yang baru: tempat
    prosa developer menumpuk kalau dibiarkan. Karena itu parameternya dibatasi
    keras dan tidak boleh ditambah untuk mengakomodasi teks penjelasan lebih
    panjang. Tidak pernah `st.error`/`st.warning` -- keadaan kosong bukan
    kesalahan.
    """
    token_ikon = ikon or IKON_KOSONG_DEFAULT
    with st.container(border=True):
        st.markdown(f"{token_ikon} :gray[{keadaan}]")
        if terakhir:
            st.markdown(f":gray[{terakhir}]")
