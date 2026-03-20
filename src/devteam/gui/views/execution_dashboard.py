from datetime import timedelta
import streamlit as st
from devteam.gui.components import render_agent_timeline, render_task_progress, render_communication_log, render_workspace_files, render_phase_tracker
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
        tab_log, tab_files, tab_specs, tab_report = st.tabs(['💬 Communication Log', '📁 Workspace Files', '📋 Specs', '📝 Final Report'])
        with tab_log:
            render_communication_log()
        with tab_files:
            render_workspace_files()
        with tab_specs:
            specs = st.session_state.get('specs', '')
            if specs:
                st.markdown(specs)
            else:
                st.caption('Specs not yet generated.')
        with tab_report:
            report = st.session_state.get('final_report', '')
            if report:
                st.markdown(report)
            else:
                st.caption('Report not yet available.')

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
