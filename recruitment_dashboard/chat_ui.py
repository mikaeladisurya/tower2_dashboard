from __future__ import annotations

import time
from typing import Any

import streamlit as st

import chat_store
from chatbot import answer_question, build_conversation_context, check_llm_connection, update_chat_summary

LLM_STATUS_TTL_SECONDS = 300

SUGGESTIONS = [
    "Bagaimana tren pendaftaran per bulan?",
    "Tahap mana yang paling banyak menggagalkan kandidat?",
    "Sebutkan 5 unit dengan kebutuhan tambahan pekerja terbanyak",
    "Sebutkan 3 wilayah dengan proporsi kandidat gagal tertinggi dibanding jumlah pendaftarnya",
    "Sebutkan 3 wilayah dengan proporsi kandidat tandatangan kontrak tertinggi dibanding jumlah pendaftarnya",
]


def get_selected_profile(llm_profiles: list[dict[str, str]]) -> dict[str, str] | None:
    """Currently active LLM profile, shared across the popover and the Chatbot page via the
    `copilot_llm_profile` widget key - falls back to the first configured profile."""
    if not llm_profiles:
        return None
    profile_by_id = {p["id"]: p for p in llm_profiles}
    selected_id = st.session_state.get("copilot_llm_profile")
    if selected_id not in profile_by_id:
        selected_id = llm_profiles[0]["id"]
    return profile_by_id[selected_id]


def render_model_status_selector(llm_profiles: list[dict[str, str]]) -> dict[str, str] | None:
    """Selectbox + connection status/recheck, shared between the popover (other pages) and
    the Chatbot page's own model-settings popover - one source of truth for the active model."""
    if not llm_profiles:
        st.caption("⚪ Mode demo tanpa API")
        return None

    profile_by_id = {p["id"]: p for p in llm_profiles}
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
    return selected_profile


def render_turn(
    question: str,
    response: dict[str, Any],
    answer_icon: str,
    idx: int,
    key_prefix: str,
) -> None:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant", avatar=answer_icon):
        if response.get("sql"):
            if st.checkbox("🔍 SQL", key=f"{key_prefix}_sql_{idx}"):
                st.code(response["sql"], language="sql")
            if response.get("table") is not None:
                st.dataframe(response["table"], width="stretch", hide_index=True)
        if response.get("chart") is not None:
            st.plotly_chart(response["chart"], width="stretch", key=f"{key_prefix}_chart_{idx}")
        st.markdown(response["text"])


def submit_question(
    conversation_id: int | None,
    question: str,
    dataframes: dict[str, Any],
    chat_context: dict[str, Any],
    profile: dict[str, str] | None,
) -> int:
    """Answer `question` and persist the turn. Lazily creates a conversation on first use
    (conversation_id is None until then, e.g. right after "New Chat") so clicking New Chat
    or opening the page fresh never leaves an empty conversation behind on its own - only an
    actual question does. Returns the conversation id the turn was saved under, so callers
    can update `st.session_state["active_conversation_id"]`."""
    if conversation_id is None:
        conversation_id = chat_store.create_conversation()
        st.session_state["active_conversation_id"] = conversation_id

    conv = chat_store.get_conversation(conversation_id) or {"chat_summary": "", "summary_upto": 0}
    history_before = chat_store.load_turns(conversation_id)
    buffer_turns = [(q, r) for q, r, _icon in history_before[-2:]]
    summary = conv.get("chat_summary") or ""
    conversation_context = build_conversation_context(summary, buffer_turns)

    response = answer_question(
        question,
        chat_context,
        dataframes,
        profile=profile,
        conversation_context=conversation_context,
    )
    # Only credit the selected model's icon when it actually produced the answer (kind
    # "llm") - "local"/"fallback" answers come from the rule engine, not the LLM.
    if response.get("kind") == "llm" and profile:
        answer_icon = profile["icon"]
    else:
        answer_icon = "😊"
    chat_store.append_turn(conversation_id, question, response, answer_icon)

    # Fold turns that just fell out of the 2-turn buffer into the rolling summary, so
    # older context survives without resending the full transcript every question.
    history_after = chat_store.load_turns(conversation_id)
    summarized_upto = conv.get("summary_upto") or 0
    foldable_end = len(history_after) - 2
    if foldable_end > summarized_upto:
        new_turns = [(q, r) for q, r, _icon in history_after[summarized_upto:foldable_end]]
        new_summary = update_chat_summary(summary, new_turns, profile)
        chat_store.update_summary(conversation_id, new_summary, foldable_end)

    return conversation_id
