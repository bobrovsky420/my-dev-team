import streamlit as st


def render_hitl_input():
    """Render the HITL input area when the crew is waiting for human input."""
    if not st.session_state.get('hitl_pending'):
        return

    question = st.session_state.get('hitl_question', 'The team needs your input.')
    hitl_ext = st.session_state.get('hitl_extension')

    st.warning('🛑 **The crew needs your input before continuing.**')
    st.markdown(f"**Question:** {question}")

    answer = st.text_area(
        'Your Answer',
        key='hitl_answer_input',
        placeholder='Type your response here...',
    )

    col_submit, col_abort, _ = st.columns([1, 1, 3])
    with col_submit:
        if st.button('✅ Submit', type='primary', key='hitl_submit'):
            if answer.strip() and hitl_ext:
                hitl_ext.submit_response(answer.strip())
                st.session_state['hitl_pending'] = False
                st.session_state['hitl_question'] = ''
                st.rerun()
            elif not answer.strip():
                st.error('Please enter a response.')
    with col_abort:
        if st.button('❌ Abort', key='hitl_abort'):
            if hitl_ext:
                hitl_ext.abort()
                st.session_state['hitl_pending'] = False
                st.session_state['hitl_question'] = ''
                st.rerun()
