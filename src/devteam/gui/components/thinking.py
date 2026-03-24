import streamlit as st

_THINKING_CSS = """
<style>
.thinking-outer {
    display: flex;
    flex-direction: column-reverse;
    height: calc(100vh - 28rem);
    overflow-y: auto;
    background-color: #262730;
    border-radius: 0.5rem;
    padding: 1rem;
}
.thinking-inner {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Source Code Pro', monospace;
    font-size: 0.85rem;
    line-height: 1.6;
    color: #fafafa;
}
.thinking-inner hr {
    border: none;
    border-top: 1px solid #444;
    margin: 0.75rem 0;
}
</style>
"""

def render_thinking_stream():
    thinking_text = st.session_state.get('thinking_text', '')
    is_active = st.session_state.get('thinking_active', False)
    if is_active:
        st.caption('🧠 Thinking in progress...')
    if thinking_text:
        import html as html_mod
        escaped = html_mod.escape(thinking_text.strip())
        escaped = escaped.replace('---', '<hr>')
        st.markdown(
            f'{_THINKING_CSS}<div class="thinking-outer"><div class="thinking-inner">{escaped}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption('No thinking output yet.')
