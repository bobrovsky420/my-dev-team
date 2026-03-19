import threading
import time
from queue import Queue
import streamlit as st
from devteam import settings
from devteam.gui.execution import get_providers_from_config, run_crew_in_thread
from devteam.gui.session import reset_execution_state
from devteam.utils import parse_spec_from_string

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
