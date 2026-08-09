from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import chat_store
import chat_ui
from chatbot import build_chat_context, list_llm_profiles
from dashboard_common import GREY, LIGHT_BLUE, PLN_BLUE, PLN_DARK, PLN_YELLOW
from data_layer import (
    build_funnel,
    load_demo_data,
    method_performance,
    placement_detail,
    region_fulfilment,
    selected_application_ids,
    stage_performance,
    vacancy_fulfilment,
)


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"


st.set_page_config(
    page_title="PLN Recruitment Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

is_dark = (st.context.theme.type or "light") == "dark"
CARD_BG = "#132C42" if is_dark else "#FFFFFF"
CARD_BORDER = "#1E3A52" if is_dark else "#E7ECF2"
CARD_SHADOW = "rgba(0, 0, 0, 0.35)" if is_dark else "rgba(16, 58, 93, 0.05)"
HEADING_COLOR = "#EAF4FF" if is_dark else PLN_DARK
BADGE_BG = "#173A57" if is_dark else LIGHT_BLUE
BADGE_TEXT = "#BFE3FF" if is_dark else PLN_DARK
POPOVER_BG = "#24272C" if is_dark else "#FFFFFF"
POPOVER_BORDER = "#3A3F46" if is_dark else "#E7ECF2"

st.markdown(
    f"""
    <style>
      .block-container {{ padding-bottom: 2rem; }}
      h1, h2, h3 {{ color: {HEADING_COLOR}; }}
      [data-testid="stMetric"] {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 3px 12px {CARD_SHADOW};
      }}
      .hero {{
        background: linear-gradient(110deg, {PLN_DARK}, {PLN_BLUE});
        color: white;
        border-radius: 18px;
        padding: 22px 26px;
        margin-bottom: 18px;
      }}
      .hero h1 {{ color: white; margin: 0; font-size: 1.8rem; }}
      .hero p {{ margin: 6px 0 0 0; opacity: .88; }}
      .insight {{
        background: {CARD_BG};
        border-left: 5px solid {PLN_YELLOW};
        border-radius: 10px;
        padding: 13px 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 10px {CARD_SHADOW};
      }}
      .demo-badge {{
        display: inline-block;
        background: {BADGE_BG};
        color: {BADGE_TEXT};
        padding: 5px 10px;
        border-radius: 999px;
        font-size: .78rem;
        font-weight: 700;
      }}
      .small-note {{ color: {GREY}; font-size: .83rem; }}

      .st-key-floating_chatbot {{
        position: fixed;
        right: 28px;
        bottom: 28px;
        z-index: 999999;
      }}
      .st-key-floating_chatbot button {{
        border-radius: 999px !important;
        background: linear-gradient(110deg, {PLN_DARK}, {PLN_BLUE}) !important;
        color: white !important;
        border: none !important;
        padding: 12px 22px !important;
        box-shadow: 0 10px 28px rgba(16, 58, 93, 0.4) !important;
      }}
      [data-testid="stPopoverBody"] {{
        width: 560px;
        max-width: 92vw;
        max-height: 82vh;
        overflow-y: auto;
        border-radius: 16px;
        background: {POPOVER_BG};
        border: 1px solid {POPOVER_BORDER};
        box-shadow: 0 16px 44px {CARD_SHADOW};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Memuat data demo...")
def get_data() -> dict[str, pd.DataFrame]:
    return load_demo_data(DATA_DIR)


data = get_data()
apps = data["applications"]
vacancies = data["vacancies"]
pipeline = data["pipeline"]

sql_dataframes = {
    "applications": apps,
    "vacancies": vacancies,
    "pipeline": pipeline,
    "contracts": data["contracts"],
}


with st.sidebar:
    st.markdown("## ⚡ PLN Recruitment")
    st.markdown('<span class="demo-badge">SYNTHETIC DEMO DATA</span>', unsafe_allow_html=True)
    st.write("")
    st.markdown("### Filter")
    programs = st.multiselect(
        "Program Rekrutmen",
        sorted(apps["NAMA REKRUTMEN"].dropna().unique()),
        placeholder="Semua program",
    )
    regions = st.multiselect(
        "Wilayah Rencana",
        sorted(apps["REGION_PLAN"].dropna().unique()),
        placeholder="Semua wilayah",
    )
    methods = st.multiselect(
        "Metode Rekrutmen",
        sorted(apps["RECRUITMENT_METHOD"].dropna().unique()),
        placeholder="Semua metode",
    )

ids = selected_application_ids(apps, programs, regions, methods)
if not ids:
    st.warning("Tidak ada data yang sesuai dengan kombinasi filter yang dipilih.")
    st.stop()
scoped_apps = apps[apps["ID_PENDAFTARAN"].isin(ids)].copy()
scoped_pipeline = pipeline[pipeline["ID_PENDAFTARAN"].isin(ids)].copy()
funnel = build_funnel(pipeline, ids)
stage_summary = stage_performance(pipeline, ids)
method_summary = method_performance(apps, pipeline, ids)
vacancy_summary = vacancy_fulfilment(vacancies, apps, ids, programs, regions)
region_summary = region_fulfilment(vacancy_summary)
placements = placement_detail(apps, ids)

applicants = len(scoped_apps)
interview_passed = int(scoped_apps["INTERVIEW_RESULT"].eq("LOLOS").sum())
signed = int(scoped_apps["CONTRACT_STATUS"].eq("SIGNED").sum())
active = int(scoped_pipeline["STAGE_STATUS"].eq("IN_PROGRESS").sum())
applicant_to_contract = signed / applicants if applicants else 0
quota = int(vacancy_summary["QUOTA"].sum())
quota_fulfilment = int(vacancy_summary["SIGNED"].sum()) / quota if quota else 0
alignment = placements["EXACT_PLACEMENT_MATCH"].mean() if len(placements) else 0

overview_context = {
    "applicants": applicants,
    "interview_passed": interview_passed,
    "signed": signed,
    "active": active,
    "applicant_to_contract": applicant_to_contract,
    "quota_fulfilment": quota_fulfilment,
    "placement_alignment": alignment,
    "filters": {"programs": programs, "regions": regions, "methods": methods},
}
chat_context = build_chat_context(
    overview_context,
    stage_summary,
    method_summary,
    region_summary,
    vacancy_summary,
)

st.session_state["dashboard_ctx"] = {
    "apps": apps,
    "vacancies": vacancies,
    "pipeline": pipeline,
    "ids": ids,
    "scoped_apps": scoped_apps,
    "scoped_pipeline": scoped_pipeline,
    "funnel": funnel,
    "stage_summary": stage_summary,
    "method_summary": method_summary,
    "vacancy_summary": vacancy_summary,
    "region_summary": region_summary,
    "placements": placements,
    "applicants": applicants,
    "interview_passed": interview_passed,
    "signed": signed,
    "active": active,
    "applicant_to_contract": applicant_to_contract,
    "quota": quota,
    "quota_fulfilment": quota_fulfilment,
    "alignment": alignment,
    "programs": programs,
    "regions": regions,
    "methods": methods,
    "sql_dataframes": sql_dataframes,
    "chat_context": chat_context,
}

if "active_conversation_id" not in st.session_state:
    # Every fresh session starts in draft mode (None), like ChatGPT/Claude's "New chat" -
    # a conversation row is only ever created lazily, on the first actual question asked.
    st.session_state["active_conversation_id"] = None
active_conversation_id = st.session_state["active_conversation_id"]

nav = st.navigation(
    [
        st.Page("app_pages/ringkasan.py", title="Ringkasan", icon=":material/dashboard:"),
        st.Page("app_pages/pipeline_metode.py", title="Pipeline & Metode", icon=":material/timeline:"),
        st.Page("app_pages/sebaran_penempatan.py", title="Sebaran & Penempatan", icon=":material/map:"),
        st.Page("app_pages/kecocokan_kandidat.py", title="Kecocokan Kandidat", icon=":material/person_search:"),
        st.Page("app_pages/chatbot.py", title="RecruitMan", icon=":material/forum:"),
    ],
    position="top",
)


components.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        if (doc.__copilotShortcutBound) return;
        doc.__copilotShortcutBound = true;

        function focusChatInput() {
            let attempts = 0;
            const tryFocus = () => {
                const textarea = Array.from(doc.querySelectorAll('textarea')).find(
                    (el) => el.placeholder === 'Tanya mengenai rekrutmen...'
                );
                if (textarea && textarea.offsetParent !== null) {
                    textarea.focus();
                    return;
                }
                attempts += 1;
                if (attempts < 20) {
                    setTimeout(tryFocus, 50);
                }
            };
            tryFocus();
        }

        doc.addEventListener('keydown', function(e) {
            if (e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey && e.key === '/') {
                const btn = doc.querySelector('.st-key-floating_chatbot button');
                if (btn) {
                    e.preventDefault();
                    btn.click();
                }
            }
        });

        doc.addEventListener('click', function(e) {
            if (e.target.closest && e.target.closest('.st-key-floating_chatbot button')) {
                focusChatInput();
            }
        }, true);
    })();
    </script>
    """,
    height=0,
)

if nav.title != "RecruitMan":
    with st.popover("💬 RecruitMan", key="floating_chatbot"):
        llm_profiles = list_llm_profiles()
        if llm_profiles:
            with st.container(border=True):
                selected_profile = chat_ui.render_model_status_selector(llm_profiles)
        else:
            selected_profile = None
            st.caption("⚪ Mode demo tanpa API")

        typed_question = st.chat_input(
            "Tanya mengenai rekrutmen...",
            key="copilot_question",
        )
        if typed_question and typed_question.strip():
            active_conversation_id = chat_ui.submit_question(
                active_conversation_id, typed_question, sql_dataframes, chat_context, selected_profile
            )

        history = chat_store.load_turns(active_conversation_id)
        indexed_history = list(enumerate(history))
        recent = indexed_history[-2:]
        older = indexed_history[:-2]

        for idx, (question, response, answer_icon) in reversed(recent):
            chat_ui.render_turn(question, response, answer_icon, idx, key_prefix="popover")

        if older:
            with st.expander(f"🕑 Riwayat sebelumnya ({len(older)})"):
                for idx, (question, response, answer_icon) in reversed(older):
                    chat_ui.render_turn(question, response, answer_icon, idx, key_prefix="popover")

nav.run()
