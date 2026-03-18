import asyncio
import threading
import time
from queue import Queue
import streamlit as st
from devteam import settings
from devteam.utils import parse_spec_from_string
from devteam.gui.execution import fetch_history_async, get_existing_threads, get_providers_from_config, run_crew_in_thread
from devteam.gui.rendering import render_execution_dashboard
from devteam.gui.session import reset_execution_state

def render_start_new_project_page():
    st.header('Start a New Project')

    uploaded_file = st.file_uploader('Upload your project requirements (.txt)', type=['txt'])
    col1, col2 = st.columns(2)
    with col1:
        available_providers = get_providers_from_config()
        provider = st.selectbox('LLM Provider', available_providers)
    with col2:
        rpm = st.number_input('Rate Limit (RPM, 0 = unlimited)', min_value=0, value=0, step=10)
    timeout = st.number_input('LLM Timeout (seconds)', min_value=10, value=120, step=10)

    if uploaded_file and st.button('🚀 Launch AI Team', type='primary'):
        content = uploaded_file.read().decode('utf-8')
        project_name, requirements = parse_spec_from_string(content)

        settings.set_llm_timeout(timeout)
        reset_execution_state()

        event_queue = Queue()
        st.session_state['event_queue'] = event_queue
        result_holder = {}
        st.session_state['result_holder'] = result_holder

        worker = threading.Thread(
            target=run_crew_in_thread,
            args=(project_name, requirements, provider, rpm, event_queue, result_holder),
            daemon=True,
        )
        st.session_state['worker_thread'] = worker
        worker.start()

        st.toast(f"🚀 AI Team launched for '{project_name}'!", icon='🤖')
        time.sleep(0.5)
        st.rerun()

def render_execution_dashboard_page():
    st.header('Execution Dashboard')
    if st.session_state.get('execution_active') or st.session_state.get('active_agents'):
        render_execution_dashboard()
    else:
        st.info(
            'No execution in progress. Go to **🚀 Start New Project** to launch one, '
            'or results from a previous run will appear here.'
        )

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

def render_history_page():
    st.header('Timeline & Checkpoints')
    threads = get_existing_threads()
    if not threads:
        st.warning('No existing workspaces found.')
        return
    selected_thread = st.selectbox('Select Project Workspace', threads, key='history_thread')
    if st.button('Fetch History'):
        with st.spinner('Digging through SQLite...'):
            try:
                history_data = asyncio.run(fetch_history_async(selected_thread))
                if not history_data:
                    st.info('No history found for this thread.')
                else:
                    st.success(f'Found {len(history_data)} checkpoints!')
                    st.dataframe(
                        history_data,
                        column_config={
                            'time': st.column_config.DatetimeColumn('Timestamp', format='h:mm:ss a'),
                            'ns': 'Namespace / Subgraph',
                            'c_id': 'Checkpoint ID',
                            'node': 'Next Node',
                        },
                        use_container_width=True,
                        hide_index=True,
                    )
            except Exception as error: # pylint: disable=broad-exception-caught
                st.error(f'Failed to read database: {str(error)}')
