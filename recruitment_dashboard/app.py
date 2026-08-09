from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from chatbot import (
    answer_question,
    build_chat_context,
    build_conversation_context,
    check_llm_connection,
    list_llm_profiles,
    update_chat_summary,
)
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
      .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
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
}


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

with st.popover("💬 Recruitment Copilot", key="floating_chatbot"):
    LLM_STATUS_TTL_SECONDS = 300

    llm_profiles = list_llm_profiles()
    selected_profile = None
    if llm_profiles:
        profile_by_id = {p["id"]: p for p in llm_profiles}
        with st.container(border=True):
            status_col, recheck_col = st.columns([5, 1], vertical_alignment="bottom")
            with status_col:
                selected_id = st.selectbox(
                    "Model LLM",
                    list(profile_by_id.keys()),
                    format_func=lambda pid: f"{profile_by_id[pid]['icon']} {profile_by_id[pid]['label']}",
                    key="copilot_llm_profile",
                    label_visibility="collapsed",
                )
            selected_profile = profile_by_id[selected_id]

            status_cache = st.session_state.setdefault("copilot_llm_status", {})
            cached = status_cache.get(selected_id)
            stale = cached is None or (time.time() - cached["checked_at"] > LLM_STATUS_TTL_SECONDS)
            with recheck_col:
                force_recheck = st.button("🔄", key=f"copilot_recheck_{selected_id}", help="Cek ulang koneksi")

            if stale or force_recheck:
                with st.spinner("Mengecek koneksi..."):
                    ok, detail = check_llm_connection(selected_profile)
                status_cache[selected_id] = {"ok": ok, "detail": detail, "checked_at": time.time()}
                cached = status_cache[selected_id]

            note = f" · {selected_profile['note']}" if selected_profile.get("note") else ""
            if cached["ok"]:
                st.badge(f"Aktif{note}", icon="🟢", color="green")
            else:
                st.badge(f"Gagal terhubung{note}", icon="🔴", color="red")
                st.caption(f"⚠️ {cached['detail'][:150]}")
    else:
        st.caption("⚪ Mode demo tanpa API")

    PLACEHOLDER_SUGGESTION = "FAQ"
    suggestions = [
        "Bagaimana tren pendaftaran per bulan?",
        "Tahap mana yang paling banyak menggagalkan kandidat?",
        "Sebutkan 5 unit dengan kebutuhan tambahan pekerja terbanyak",
        "Sebutkan 3 wilayah dengan proporsi kandidat gagal tertinggi dibanding jumlah pendaftarnya",
        "Sebutkan 3 wilayah dengan proporsi kandidat tandatangan kontrak tertinggi dibanding jumlah pendaftarnya",
    ]

    def _apply_suggestion():
        choice = st.session_state.get("copilot_suggestion")
        if choice and choice != PLACEHOLDER_SUGGESTION:
            st.session_state["copilot_question"] = choice

    st.selectbox(
        "Pertanyaan Contoh",
        [PLACEHOLDER_SUGGESTION] + suggestions,
        key="copilot_suggestion",
        on_change=_apply_suggestion,
        label_visibility="collapsed",
    )
    typed_question = st.chat_input(
        "Tanya mengenai rekrutmen...",
        key="copilot_question",
    )
    if typed_question and typed_question.strip():
        history_before = st.session_state.get("chat_history", [])
        buffer_turns = [(q, r) for q, r, _icon in history_before[-2:]]
        summary = st.session_state.get("chat_summary", "")
        conversation_context = build_conversation_context(summary, buffer_turns)
        response = answer_question(
            typed_question,
            chat_context,
            sql_dataframes,
            profile=selected_profile,
            conversation_context=conversation_context,
        )
        # Only credit the selected model's icon when it actually produced the answer (kind
        # "llm") - "local"/"fallback" answers come from the rule engine, not the LLM.
        if response.get("kind") == "llm" and selected_profile:
            answer_icon = selected_profile["icon"]
        else:
            answer_icon = "😊"
        st.session_state.setdefault("chat_history", []).append((typed_question, response, answer_icon))

        # Fold turns that just fell out of the 2-turn buffer into the rolling summary, so
        # older context survives without resending the full transcript every question.
        history_after = st.session_state["chat_history"]
        summarized_upto = st.session_state.get("chat_summary_upto", 0)
        foldable_end = len(history_after) - 2
        if foldable_end > summarized_upto:
            new_turns = [(q, r) for q, r, _icon in history_after[summarized_upto:foldable_end]]
            st.session_state["chat_summary"] = update_chat_summary(summary, new_turns, selected_profile)
            st.session_state["chat_summary_upto"] = foldable_end
    history = st.session_state.get("chat_history", [])
    indexed_history = list(enumerate(history))
    recent = indexed_history[-2:]
    older = indexed_history[:-2]

    for idx, (question, response, answer_icon) in reversed(recent):
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar=answer_icon):
            if response.get("sql"):
                if st.checkbox("🔍 SQL", key=f"copilot_show_sql_{idx}"):
                    st.code(response["sql"], language="sql")
                if response.get("table") is not None:
                    st.dataframe(response["table"], width="stretch", hide_index=True)
            if response.get("chart") is not None:
                st.plotly_chart(response["chart"], width="stretch", key=f"copilot_chart_{idx}")
            st.markdown(response["text"])

    if older:
        with st.expander(f"🕑 Riwayat sebelumnya ({len(older)})"):
            for idx, (question, response, answer_icon) in reversed(older):
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar=answer_icon):
                    if response.get("sql"):
                        if st.checkbox("🔍 SQL", key=f"copilot_show_sql_{idx}"):
                            st.code(response["sql"], language="sql")
                        if response.get("table") is not None:
                            st.dataframe(response["table"], width="stretch", hide_index=True)
                    if response.get("chart") is not None:
                        st.plotly_chart(response["chart"], width="stretch", key=f"copilot_chart_{idx}")
                    st.markdown(response["text"])


nav = st.navigation(
    [
        st.Page("app_pages/ringkasan.py", title="Ringkasan", icon=":material/dashboard:"),
        st.Page("app_pages/pipeline_metode.py", title="Pipeline & Metode", icon=":material/timeline:"),
        st.Page("app_pages/sebaran_penempatan.py", title="Sebaran & Penempatan", icon=":material/map:"),
        st.Page("app_pages/kecocokan_kandidat.py", title="Kecocokan Kandidat", icon=":material/person_search:"),
    ],
    position="top",
)
nav.run()
