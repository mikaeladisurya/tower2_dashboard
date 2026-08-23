"""Dashboard Rekrutmen PLN v3 -- titik masuk aplikasi.

Menyusun navigasi, pemilih tanggal lintas halaman, lalu menjalankan halaman
terpilih. Logika data ada di `core/`, tampilan bersama di `components/`, isi
halaman di `app_pages/`.
"""

from __future__ import annotations

import streamlit as st

from chat import chat_store, chat_ui
from chat.chatbot import list_llm_profiles
from components.tampilan import keadaan_kosong
from core import db

st.set_page_config(
    page_title="Dashboard Rekrutmen PLN",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Penjagaan database di batas aplikasi -- `core/db.py` melempar FileNotFoundError
# yang menyebut jalur internal & perintah build; itu galat setup yang sah di sisi
# modul, tapi tidak boleh bocor mentah ke layar pengguna (P2).
try:
    db.koneksi()
except FileNotFoundError:
    st.title("Dashboard Rekrutmen PLN")
    keadaan_kosong("Data belum tersedia")
    st.stop()

HALAMAN = [
    st.Page("app_pages/beranda.py", title="Beranda", icon=":material/home:", default=True),
    st.Page(
        "app_pages/perencanaan.py",
        title="Perencanaan Formasi",
        icon=":material/event_upcoming:",
    ),
    st.Page(
        "app_pages/seleksi.py", title="Seleksi Berjalan", icon=":material/pending_actions:"
    ),
    st.Page("app_pages/corong.py", title="Corong Seleksi", icon=":material/filter_alt:"),
    st.Page(
        "app_pages/pasca.py", title="Pasca-Seleksi", icon=":material/workspace_premium:"
    ),
    st.Page(
        "app_pages/rencana_realisasi.py", title="Rencana & Realisasi", icon=":material/balance:"
    ),
    st.Page("app_pages/profil.py", title="Profil Pelamar", icon=":material/groups:"),
    st.Page("app_pages/eksplorasi.py", title="Eksplorasi", icon=":material/science:"),
    st.Page("app_pages/chatbot.py", title="RecruitMan", icon=":material/smart_toy:"),
]

halaman = st.navigation(HALAMAN, position="sidebar")

with st.sidebar:
    st.date_input("Lihat per tanggal", key=db.KUNCI_TANGGAL, value=db.hari_ini())

# -- Popover RecruitMan mengambang (semua halaman kecuali halaman RecruitMan
# sendiri) -- port dari recruitment_dashboardv2/streamlit_app.py. Tombol posisi
# tetap di pojok kanan bawah lewat CSS (.st-key-floating_chatbot), supaya bisa
# tanya tanpa pindah halaman. Riwayat percakapan dibagi dengan halaman RecruitMan
# penuh lewat session_state["active_conversation_id"] yang sama.
#
# Warna gradien: v2 mengambilnya dari `core/theme.py` yang tidak diport ke v3.
# Dua warna di bawah adalah `primaryColor` [theme.light] dan [theme.dark] di
# .streamlit/config.toml, dipilih urutannya menurut mode aktif.
_gelap = (st.context.theme.type or "light") == "dark"
_gradien_a, _gradien_b = ("#479EF5", "#0078D4") if _gelap else ("#0078D4", "#479EF5")
st.html(
    f"""
    <style>
      .st-key-floating_chatbot {{
        position: fixed;
        right: 28px;
        bottom: 28px;
        z-index: 999999;
      }}
      .st-key-floating_chatbot button {{
        border-radius: 999px !important;
        background: linear-gradient(110deg, {_gradien_a}, {_gradien_b}) !important;
        color: white !important;
        border: none !important;
        padding: 12px 22px !important;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.25) !important;
      }}
    </style>
    """
)

if halaman.title != "RecruitMan":
    with st.popover("RecruitMan", icon=":material/chat:", key="floating_chatbot"):
        llm_profiles = list_llm_profiles()
        if llm_profiles:
            with st.container(border=True):
                selected_profile = chat_ui.render_model_status_selector(
                    llm_profiles, show_new_chat_button=True, auto_check=False
                )
        else:
            selected_profile = None
            st.caption("Mode demo -- belum ada model bahasa yang tersambung")

        active_conversation_id = st.session_state.setdefault("active_conversation_id", None)

        typed_question = st.chat_input("Tanya mengenai rekrutmen...", key="copilot_question")
        just_answered = False
        if typed_question and typed_question.strip():
            active_conversation_id = chat_ui.submit_question(
                active_conversation_id, typed_question, selected_profile, key_prefix="popover"
            )
            just_answered = True

        history = chat_store.load_turns(active_conversation_id)
        indexed_history = list(enumerate(history))
        # Giliran yang baru dijawab sudah digambar langsung oleh submit_question, tepat
        # di atas sini -- dibuang di sini supaya tidak digambar dua kali.
        if just_answered:
            indexed_history = indexed_history[:-1]
        recent = indexed_history[-2:]
        older = indexed_history[:-2]

        for idx, (question, response, answer_icon, created_at) in reversed(recent):
            chat_ui.render_turn(
                question, response, answer_icon, idx, key_prefix="popover", created_at=created_at
            )

        if older:
            with st.expander(f"Riwayat sebelumnya ({len(older)})"):
                for idx, (question, response, answer_icon, created_at) in reversed(older):
                    chat_ui.render_turn(
                        question, response, answer_icon, idx, key_prefix="popover", created_at=created_at
                    )

halaman.run()
