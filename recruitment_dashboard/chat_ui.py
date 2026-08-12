from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

import chat_store
from chatbot import (
    answer_question,
    build_conversation_context,
    check_llm_connection,
    run_sql_for_export,
    update_chat_summary,
)

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


def render_model_status_selector(
    llm_profiles: list[dict[str, str]],
    show_new_chat_button: bool = False,
) -> dict[str, str] | None:
    """Selectbox + connection status/recheck, shared between the popover (other pages) and
    the Chatbot page's own model card - one source of truth for the active model. The popover
    additionally gets a compact "New Chat" icon button next to the recheck button (the full
    RecruitMan page already has its own full-width "New Chat" button in the sidebar, so it
    doesn't need a second one here)."""
    if not llm_profiles:
        st.caption("⚪ Mode demo tanpa API")
        return None

    profile_by_id = {p["id"]: p for p in llm_profiles}
    if show_new_chat_button:
        status_col, recheck_col, new_chat_col = st.columns([4, 1, 1], vertical_alignment="bottom")
    else:
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
    if show_new_chat_button:
        with new_chat_col:
            if st.button(
                "", icon=":material/add:", key="popover_new_chat", help="Percakapan baru"
            ):
                st.session_state["active_conversation_id"] = None
                st.rerun()

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


def _format_turn_time(created_at: str | None) -> str:
    """Best-effort local-time label for a turn. created_at is stored in UTC and marks when
    the turn finished saving (right after the answer was ready), not the exact instant the
    question was typed - close enough for a rough timestamp, not precise to the second."""
    if not created_at:
        return ""
    try:
        dt = datetime.fromisoformat(created_at)
    except ValueError:
        return ""
    tz_name = st.context.timezone
    if tz_name:
        try:
            dt = dt.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass
    return dt.strftime("%d/%m/%Y %H:%M")


def _render_export_button(
    block: dict[str, Any],
    dataframes: dict[str, Any] | None,
    export_key: str,
) -> None:
    """Offer a "download all rows" button only when the displayed table was actually
    truncated to the in-chat preview cap - if total_rows is unknown (older saved turns) or
    not greater than what's already shown, the native download icon on st.dataframe already
    covers it, so a second button would just be a confusing duplicate."""
    total_rows = block.get("total_rows")
    table = block.get("table")
    if not total_rows or table is None or total_rows <= len(table) or not block.get("sql"):
        return
    if not dataframes:
        return

    if export_key not in st.session_state:
        if st.button(
            f"⬇️ Siapkan semua {total_rows:,} baris (CSV)".replace(",", "."),
            key=f"{export_key}_prepare",
        ):
            with st.spinner("Menyiapkan file..."):
                try:
                    full_table = run_sql_for_export(block["sql"], dataframes)
                    st.session_state[export_key] = full_table.to_csv(index=False).encode("utf-8")
                except Exception as exc:
                    st.error(f"Gagal menyiapkan file: {exc}")
                    return
            st.rerun()
    else:
        st.download_button(
            f"⬇️ Download semua {total_rows:,} baris (CSV)".replace(",", "."),
            data=st.session_state[export_key],
            file_name=f"{export_key}.csv",
            mime="text/csv",
            key=f"{export_key}_download",
        )


def render_turn(
    question: str,
    response: dict[str, Any],
    answer_icon: str,
    idx: int,
    key_prefix: str,
    created_at: str | None = None,
    dataframes: dict[str, Any] | None = None,
) -> None:
    with st.chat_message("user"):
        st.markdown(question)
        time_label = _format_turn_time(created_at)
        if time_label:
            st.caption(time_label)
    with st.chat_message("assistant", avatar=answer_icon):
        for block_idx, block in enumerate(response.get("results") or []):
            if block.get("sql"):
                if st.checkbox("🔍 SQL", key=f"{key_prefix}_sql_{idx}_{block_idx}"):
                    st.code(block["sql"], language="sql")
            if block.get("table") is not None:
                st.dataframe(block["table"], width="stretch", hide_index=True)
                _render_export_button(block, dataframes, f"{key_prefix}_export_{idx}_{block_idx}")
            if block.get("chart") is not None:
                st.plotly_chart(block["chart"], width="stretch", key=f"{key_prefix}_chart_{idx}_{block_idx}")
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
    buffer_turns = [(q, r) for q, r, _icon, _created_at in history_before[-2:]]
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
        new_turns = [(q, r) for q, r, _icon, _created_at in history_after[summarized_upto:foldable_end]]
        new_summary = update_chat_summary(summary, new_turns, profile)
        chat_store.update_summary(conversation_id, new_summary, foldable_end)

    return conversation_id
