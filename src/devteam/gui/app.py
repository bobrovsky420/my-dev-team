import streamlit as st
from devteam.utils import setup_logging
from devteam.gui import app_pages as pages
from devteam.gui.session import drain_queue, init_session_state

setup_logging(console_level=None)

def _configure_streamlit() -> None:
    try:
        st.set_option('client.showSidebarNavigation', False)
    except Exception: # pylint: disable=broad-exception-caught
        pass

def main():
    _configure_streamlit()
    st.set_page_config(page_title='My AI Dev Team', page_icon='🚀', layout='wide')
    init_session_state()

    st.title('🤖 My AI Dev Team')
    st.sidebar.title('Navigation')

    if 'nav_mode' not in st.session_state:
        st.session_state['nav_mode'] = '🏠 Welcome'

    if st.session_state.get('execution_active') and st.session_state.get('nav_mode') != '📊 Execution Dashboard':
        st.session_state['nav_mode'] = '📊 Execution Dashboard'
        st.rerun()

    mode = st.sidebar.radio(
        'Choose an action:',
        [
            '🏠 Welcome',
            '🚀 Start New Project',
            '📊 Execution Dashboard',
            '🔄 Resume Project',
            '🕰️ Show History'
        ],
        key='nav_mode',
    )

    if st.session_state.get('execution_active') or st.session_state.get('event_queue') is not None:
        drain_queue()
        worker = st.session_state.get('worker_thread')
        if worker and not worker.is_alive():
            drain_queue()
            st.session_state['execution_active'] = False

    if mode == '🏠 Welcome':
        pages.render_welcome_page()
    elif mode == '🚀 Start New Project':
        pages.render_start_new_project_page()
    elif mode == '📊 Execution Dashboard':
        pages.render_execution_dashboard_page()
    elif mode == '🔄 Resume Project':
        pages.render_resume_project_page()
    elif mode == '🕰️ Show History':
        pages.render_history_page()

if __name__ == '__main__':
    main()
