from datetime import timedelta
import streamlit as st
from devteam.gui.components import render_agent_timeline, render_task_progress, render_communication_log, render_workspace_files, render_phase_tracker, render_hitl_input, render_thinking_stream
from devteam.gui.session import drain_queue

def render_execution_dashboard_page():
    st.header('Execution Dashboard')
    if not (st.session_state.get('execution_active') or st.session_state.get('active_agents')):
        st.info(
            'No execution in progress. Go to **🚀 Start New Project** to launch one, '
            'or results from a previous run will appear here.'
        )
        return
    _live_dashboard()

@st.fragment(run_every=timedelta(seconds=1))
def _live_dashboard():
    if st.session_state.get('execution_active') or st.session_state.get('event_queue') is not None:
        drain_queue()
        worker = st.session_state.get('worker_thread')
        if worker and not worker.is_alive():
            drain_queue()
            st.session_state['execution_active'] = False

    render_phase_tracker()

    if st.session_state.get('hitl_pending'):
        render_hitl_input()

    st.divider()

    result = st.session_state.get('result_holder', {})
    is_running = st.session_state.get('execution_active', False)
    left, right = st.columns([2, 3])

    with left:
        st.subheader('Agent Activity')
        render_agent_timeline()
        st.subheader('Task Progress')
        render_task_progress()

    with right:
        tabs = ['💬 Communication Log', '📁 Workspace Files', '📋 Specs', '📝 Final Report']
        if st.session_state.get('thinking_enabled'):
            tabs.append('🧠 Thinking')
        tab_objects = st.tabs(tabs)
        with tab_objects[0]:
            render_communication_log()
        with tab_objects[1]:
            render_workspace_files()
        with tab_objects[2]:
            specs = st.session_state.get('specs', '')
            if specs:
                st.markdown(specs)
            else:
                st.caption('Specs not yet generated.')
        with tab_objects[3]:
            report = st.session_state.get('final_report', '')
            if report:
                st.markdown(report)
            else:
                st.caption('Report not yet available.')
        if st.session_state.get('thinking_enabled') and len(tab_objects) > 4:
            with tab_objects[4]:
                render_thinking_stream()

    if not is_running and result:
        st.divider()
        if 'error' in result:
            st.error(f"💥 Execution failed: {result['error']}")
        elif 'final_state' in result:
            final_state = result['final_state']
            if getattr(final_state, 'abort_requested', False):
                st.error('❌ Workflow was aborted.')
            elif getattr(final_state, 'success', False):
                st.success(f"🎉 Project completed successfully! Workspace: `{result.get('thread_id', '')}`")
                st.balloons()
            else:
                st.warning('🚨 Release failed — integration bugs found.')
                for bug in getattr(final_state, 'integration_bugs', []):
                    st.warning(f'- {bug}')
