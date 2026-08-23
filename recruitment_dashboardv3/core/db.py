"""Akses ke rekrutmen.duckdb -- satu-satunya pintu masuk data.

Database dibuka **read-only** dan tidak pernah dimuat ke memori sebagai DataFrame:
isinya 4,22 juta baris. Yang di-cache adalah hasil query, bukan tabelnya.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pandas as pd
import streamlit as st

# core/ -> recruitment_dashboardv3/ -> tower2_dashboard/
DB_PATH = Path(__file__).resolve().parents[2] / "mockdb" / "out" / "rekrutmen.duckdb"

# Kunci session_state yang menampung tanggal acuan hasil pemilih tanggal (dipilih
# pengguna). Satu konstanta, dipakai seragam oleh seluruh halaman.
KUNCI_TANGGAL = "tanggal_acuan"


def _pastikan_db_ada() -> None:
    """Galat setup, bukan galat pengguna -- hanya terpicu kalau DB belum dibangun."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database tidak ditemukan di {DB_PATH}. "
            "Jalankan `python mockdb/build_all.py` untuk membangunnya."
        )


@st.cache_resource
def koneksi() -> duckdb.DuckDBPyConnection:
    """Satu koneksi read-only dipakai bersama seluruh sesi."""
    _pastikan_db_ada()
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    """Jalankan SQL dan kembalikan DataFrame.

    Memakai `.cursor()` supaya tiap pemanggilan punya kursor sendiri -- koneksi
    DuckDB dipakai bersama antar sesi Streamlit lewat cache_resource.
    """
    return koneksi().cursor().execute(sql, list(params or [])).df()


@st.cache_data(ttl=3600, show_spinner=False)
def skalar(sql: str, params: Sequence[Any] | None = None) -> Any:
    """Ambil satu nilai tunggal dari query."""
    hasil = koneksi().cursor().execute(sql, list(params or [])).fetchone()
    return hasil[0] if hasil else None


@lru_cache(maxsize=1)
def _baca_tanggal_potong() -> date:
    """Baca tanggal potong dari `_meta_generator`, tanpa lewat `@st.cache_data`.

    Memakai koneksi duckdb langsung, bukan `query()`/`skalar()`, supaya bisa
    dipanggil di luar konteks Streamlit (skrip verifikasi, tes headless).
    """
    _pastikan_db_ada()
    koneksi_langsung = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        hasil = koneksi_langsung.execute(
            "SELECT nilai FROM _meta_generator WHERE kunci = 'tanggal_sekarang'"
        ).fetchone()
    finally:
        koneksi_langsung.close()
    return date.fromisoformat(hasil[0])


def __getattr__(nama: str) -> Any:
    """`db.TANGGAL_POTONG` dibaca saat pertama diakses, bukan saat modul diimpor.

    Penanda horison data -- BUKAN patokan tampilan. Peran "hari ini" seluruh
    dashboard ada di `hari_ini()`, bukan di sini. TANGGAL_POTONG hanya menandai
    batas tanggal terjauh yang disimulasikan generator data mock.

    Dibuat malas (PEP 562) supaya mengimpor modul ini tidak menyentuh database.
    Tanpa ini, tiap tes yang mengimpor `core.db` -- termasuk yang sama sekali
    tidak butuh tanggal potong -- ikut gagal keras kalau berkas DB tidak ada.
    """
    if nama == "TANGGAL_POTONG":
        return _baca_tanggal_potong()
    raise AttributeError(f"module {__name__!r} tidak punya atribut {nama!r}")


def hari_ini() -> date:
    """Jangkar waktu seluruh dashboard.

    Default tanggal berjalan sungguhan (`date.today()`); bisa ditimpa pemilih
    tanggal lewat `st.session_state[KUNCI_TANGGAL]`. Satu-satunya tempat di v3
    yang boleh memanggil `date.today()` -- semua halaman wajib lewat fungsi ini
    supaya pemilih tanggal berlaku seragam.

    Aman dipanggil di luar konteks Streamlit (skrip verifikasi, tes headless):
    akses ke `st.session_state` di luar app run bisa melempar, jatuhkan ke
    `date.today()`.
    """
    try:
        override = st.session_state.get(KUNCI_TANGGAL)
        if override is not None:
            return override
    except Exception:
        pass
    return date.today()


def jendela(hari: int) -> tuple[date, date]:
    """Rentang `(hari_ini() - hari, hari_ini())` -- helper P3.

    Terikat ke `hari_ini()`, bukan `TANGGAL_POTONG`, supaya "N hari terakhir"
    tidak pernah jatuh ke `max(tanggal)` dari data.
    """
    acuan = hari_ini()
    return acuan - timedelta(days=hari), acuan
