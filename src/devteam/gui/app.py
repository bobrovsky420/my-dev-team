import streamlit as st
from devteam.utils import setup_logging
from devteam.gui.pages import (
    render_execution_dashboard_page,
    render_history_page,
    render_resume_project_page,
    render_start_new_project_page,
)
from devteam.gui.session import drain_queue, init_session_state

setup_logging(console_level=None)

def main():
    st.set_page_config(page_title='My AI Dev Team', page_icon='🚀', layout='wide')
    init_session_state()

    st.title('🤖 My AI Dev Team')
    st.sidebar.title('Navigation')

    if st.session_state.get('execution_active') and st.session_state.get('nav_mode') != '📊 Execution Dashboard':
        st.session_state['nav_mode'] = '📊 Execution Dashboard'
        st.rerun()

    mode = st.sidebar.radio(
        'Choose an action:',
        ['🚀 Start New Project', '📊 Execution Dashboard', '🔄 Resume Project', '🕰️ View History'],
        key='nav_mode',
    )

    if st.session_state.get('execution_active') or st.session_state.get('event_queue') is not None:
        drain_queue()
        worker = st.session_state.get('worker_thread')
        if worker and not worker.is_alive():
            drain_queue()
            st.session_state['execution_active'] = False

    if mode == '🚀 Start New Project':
        render_start_new_project_page()
    elif mode == '📊 Execution Dashboard':
        render_execution_dashboard_page()
    elif mode == '🔄 Resume Project':
        render_resume_project_page()
    elif mode == '🕰️ View History':
        render_history_page()

if __name__ == '__main__':
    main()
