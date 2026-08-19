"""Akses ke rekrutmen.duckdb — satu-satunya pintu masuk data.

Database dibuka **read-only** dan tidak pernah dimuat ke memori sebagai DataFrame:
isinya 4,22 juta baris. Yang di-cache adalah hasil query, bukan tabelnya.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pandas as pd
import streamlit as st

# core/ -> recruitment_dashboardv2/ -> tower2_dashboard/
DB_PATH = Path(__file__).resolve().parents[2] / "mockdb" / "out" / "rekrutmen.duckdb"

# Tanggal potong data. Semua status ("sedang OJT", "belum SK") dihitung relatif ke sini.
TANGGAL_POTONG = date(2026, 9, 15)


@st.cache_resource
def koneksi() -> duckdb.DuckDBPyConnection:
    """Satu koneksi read-only dipakai bersama seluruh sesi."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database tidak ditemukan di {DB_PATH}. "
            "Jalankan `python mockdb/build_all.py` untuk membangunnya."
        )
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    """Jalankan SQL dan kembalikan DataFrame.

    Memakai `.cursor()` supaya tiap pemanggilan punya kursor sendiri — koneksi
    DuckDB dipakai bersama antar sesi Streamlit lewat cache_resource.
    """
    return koneksi().cursor().execute(sql, list(params or [])).df()


@st.cache_data(ttl=3600, show_spinner=False)
def skalar(sql: str, params: Sequence[Any] | None = None) -> Any:
    """Ambil satu nilai tunggal dari query."""
    hasil = koneksi().cursor().execute(sql, list(params or [])).fetchone()
    return hasil[0] if hasil else None


def daftar_tabel() -> list[str]:
    """Nama seluruh tabel — dipakai chatbot untuk membangun prompt skema."""
    df = query(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' ORDER BY 1"
    )
    return df["table_name"].tolist()
