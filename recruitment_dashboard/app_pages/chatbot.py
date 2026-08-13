from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

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
            label_col, menu_col = st.columns([5, 1], vertical_alignment="center")
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
            with menu_col:
                with st.popover("", key=f"chatpage_menu_{conv['id']}"):
                    new_title = st.text_input(
                        "Ubah judul",
                        value=label,
                        key=f"chatpage_rename_{conv['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button("Simpan judul", key=f"chatpage_rename_save_{conv['id']}", width="stretch"):
                        chat_store.update_title(conv["id"], new_title.strip() or "Percakapan baru")
                        st.rerun()
                    if st.button(
                        "🗑 Hapus percakapan", key=f"chatpage_del_{conv['id']}", width="stretch"
                    ):
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

    prefill = st.session_state.pop("chatpage_prefill", None)
    if prefill:
        # st.chat_input has no `value`/default param (unsupported by the widget itself), so
        # a suggestion click can't natively pre-fill it - this drops the text into the
        # underlying textarea via JS instead, same window.parent.document technique already
        # used for the Ctrl+/ shortcut in app.py, leaving it editable for the user to tweak
        # before pressing Enter themselves (nothing is submitted here).
        components.html(
            """
            <script>
            (function() {
                const doc = window.parent.document;
                const text = __TEXT_JSON__;
                let attempts = 0;
                function trySet() {
                    const textarea = Array.from(doc.querySelectorAll('textarea')).find(
                        (el) => el.placeholder === 'Tanya mengenai rekrutmen...'
                    );
                    if (textarea) {
                        const setter = Object.getOwnPropertyDescriptor(
                            window.parent.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        setter.call(textarea, text);
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        textarea.focus();
                        return;
                    }
                    attempts += 1;
                    if (attempts < 20) {
                        setTimeout(trySet, 50);
                    }
                }
                trySet();
            })();
            </script>
            """.replace("__TEXT_JSON__", json.dumps(prefill)),
            height=0,
        )

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
                    # Prefill only - the question isn't asked until the user reviews/edits
                    # it in the chat input and presses Enter themselves.
                    st.session_state["chatpage_prefill"] = suggestion
                    st.rerun()
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
