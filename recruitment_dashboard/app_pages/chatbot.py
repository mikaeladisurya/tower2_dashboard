from __future__ import annotations

import streamlit as st

import chat_store
import chat_ui
from chatbot import list_llm_profiles
from dashboard_common import get_ctx

ctx = get_ctx()
sql_dataframes = ctx["sql_dataframes"]
chat_context = ctx["chat_context"]

llm_profiles = list_llm_profiles()
selected_profile = chat_ui.get_selected_profile(llm_profiles)

active_id = st.session_state.setdefault("active_conversation_id", None)

left, right = st.columns([1, 3])

with left:
    with st.container(border=True):
        if st.button("＋ New Chat", width="stretch"):
            # Draft mode - no conversation row until the first question is actually asked.
            st.session_state["active_conversation_id"] = None
            st.rerun()
        selected_profile = chat_ui.render_model_status_selector(llm_profiles)

    st.markdown("#### Riwayat")
    # Bounded + independently scrollable (CSS in app.py, .st-key-chatpage_history_box) so a
    # long history never grows past the window and forces a page-level scroll.
    with st.container(key="chatpage_history_box", border=True):
        for conv in chat_store.list_conversations():
            is_active = conv["id"] == active_id
            label_col, delete_col = st.columns([5, 1], vertical_alignment="center")
            label = conv["title"] or "Percakapan baru"
            with label_col:
                if st.button(
                    label,
                    key=f"chatpage_conv_{conv['id']}",
                    width="stretch",
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["active_conversation_id"] = conv["id"]
                    st.rerun()
            with delete_col:
                if st.button("🗑", key=f"chatpage_del_{conv['id']}", help="Hapus percakapan"):
                    chat_store.delete_conversation(conv["id"])
                    if is_active:
                        st.session_state["active_conversation_id"] = None
                    st.rerun()

with right:
    # Input first, then turns newest-first below it - same pattern as the popover, so
    # opening a past conversation shows the latest answer immediately without scrolling,
    # and the two surfaces feel consistent.
    typed_question = st.chat_input("Tanya mengenai rekrutmen...", key="chatpage_question")
    just_answered = False

    # Bounded + independently scrollable (CSS in app.py, .st-key-chatpage_answers_box), same
    # pattern as the Riwayat box - only the answers scroll, the page itself never does.
    with st.container(key="chatpage_answers_box", border=True):
        if typed_question and typed_question.strip():
            active_id = chat_ui.submit_question(
                active_id, typed_question, sql_dataframes, chat_context, selected_profile, key_prefix="chatpage"
            )
            just_answered = True

        turns = chat_store.load_turns(active_id)
        if not turns:
            st.markdown(
                '<div style="text-align:center; padding: 64px 20px 28px 20px;">'
                '<h2>💬 RecruitMan</h2>'
                '<p>Tanyakan apa saja tentang data rekrutmen PLN, atau coba salah satu contoh di bawah.</p>'
                "</div>",
                unsafe_allow_html=True,
            )
            suggestion_row = st.container(horizontal=True, horizontal_alignment="center")
            for i, suggestion in enumerate(chat_ui.SUGGESTIONS):
                if suggestion_row.button(suggestion, key=f"chatpage_suggestion_{i}"):
                    chat_ui.submit_question(
                        active_id,
                        suggestion,
                        sql_dataframes,
                        chat_context,
                        selected_profile,
                        key_prefix="chatpage",
                        render_live=False,
                    )
                    st.rerun()  # session_state["active_conversation_id"] is already updated by submit_question
        else:
            # The just-answered turn (if any) was already drawn live by submit_question, right
            # above this loop, in exactly this spot - skip it here so it isn't drawn twice.
            history_to_draw = turns[:-1] if just_answered else turns
            for idx, (question, response, answer_icon, created_at) in reversed(list(enumerate(history_to_draw))):
                chat_ui.render_turn(
                    question,
                    response,
                    answer_icon,
                    idx,
                    key_prefix="chatpage",
                    created_at=created_at,
                    dataframes=sql_dataframes,
                )
