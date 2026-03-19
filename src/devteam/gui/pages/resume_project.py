import streamlit as st
from devteam.gui.execution import get_existing_threads

def render_resume_project_page():
    st.header('Resume or Inject Feedback')
    threads = get_existing_threads()
    if not threads:
        st.warning('No existing workspaces found. Start a new project first!')
        return
    selected_thread = st.selectbox('Select Project Workspace', threads)
    st.subheader('Time Travel & Intervention')
    feedback = st.text_area('Human Feedback (Optional)', placeholder="e.g., 'Stop using SQLite and use PostgreSQL instead.'")
    col1, col2 = st.columns(2)
    with col1:
        as_node = st.selectbox('Impersonate Agent', ['reviewer', 'qa', 'pm', 'architect'])
    with col2:
        checkpoint = st.text_input('Target Checkpoint ID (Optional)', placeholder='Leave blank for latest state')
    if st.button('🔄 Resume Execution', type='primary'):
        st.success(f'Resuming `{selected_thread}`...')
        if feedback:
            st.warning(f'Injecting feedback as **{as_node.upper()}** into the graph.')
        _ = checkpoint
