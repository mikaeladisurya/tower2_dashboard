"""Dashboard Rekrutmen PLN v2 — titik masuk aplikasi.

Menyusun navigasi, elemen lintas halaman (sakelar mode analis, tanggal potong),
lalu menjalankan halaman terpilih. Logika data ada di `core/`, tampilan di
`components/`, isi halaman di `app_pages/`.
"""

from __future__ import annotations

import streamlit as st

from components import ui
from core.db import TANGGAL_POTONG

st.set_page_config(
    page_title="Dashboard Rekrutmen PLN",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="expanded",
)

HALAMAN = [
    st.Page("app_pages/ringkasan.py", title="Ringkasan", icon=":material/dashboard:", default=True),
    st.Page("app_pages/perencanaan.py", title="Perencanaan", icon=":material/event_upcoming:"),
    st.Page("app_pages/corong.py", title="Corong seleksi", icon=":material/filter_alt:"),
    st.Page("app_pages/kandidat.py", title="Kandidat", icon=":material/groups:"),
    st.Page("app_pages/pasca.py", title="Pasca-seleksi & OJT", icon=":material/school:"),
    st.Page("app_pages/penempatan.py", title="Penempatan", icon=":material/location_on:"),
    st.Page("app_pages/kualitas.py", title="Kualitas data", icon=":material/fact_check:"),
    st.Page("app_pages/chatbot.py", title="Chatbot", icon=":material/chat:"),
]

halaman = st.navigation(HALAMAN, position="sidebar")

with st.sidebar:
    ui.sakelar_mode_analis()
    st.caption(
        f"Data per {TANGGAL_POTONG.strftime('%d %B %Y')} · gelombang 2019–2025 · "
        "PLN Group"
    )

halaman.run()
