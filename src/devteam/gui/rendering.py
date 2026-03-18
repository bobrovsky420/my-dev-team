import time
import streamlit as st

PHASE_ORDER = ['Planning', 'Development', 'Integration', 'Complete']
PHASE_ICONS = {
    'Planning': '📋',
    'Development': '💻',
    'Integration': '📦',
    'Complete': '🎉',
}

def render_phase_tracker():
    current = st.session_state.get('current_phase')
    columns = st.columns(len(PHASE_ORDER))
    for index, phase in enumerate(PHASE_ORDER):
        with columns[index]:
            icon = PHASE_ICONS[phase]
            if phase == current:
                st.markdown(
                    f"<div style='text-align:center;padding:8px;background:#1a73e8;color:white;"
                    f"border-radius:8px;font-weight:bold'>{icon} {phase}</div>",
                    unsafe_allow_html=True,
                )
            elif PHASE_ORDER.index(phase) < PHASE_ORDER.index(current or PHASE_ORDER[0]):
                st.markdown(
                    f"<div style='text-align:center;padding:8px;background:#2e7d32;color:white;"
                    f"border-radius:8px'>{icon} {phase} ✓</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='text-align:center;padding:8px;background:#333;color:#888;"
                    f"border-radius:8px'>{icon} {phase}</div>",
                    unsafe_allow_html=True,
                )

def render_task_progress():
    task_progress = st.session_state['task_progress']
    if task_progress['total'] > 0:
        st.markdown(f"**Current Task:** {task_progress['name']}  ({task_progress['current']}/{task_progress['total']})")
        st.progress(task_progress['current'] / task_progress['total'])
    revision_count = st.session_state.get('revision_count', 0)
    if revision_count > 0:
        st.caption(f'Revision #{revision_count}')

def render_agent_timeline():
    agents = st.session_state.get('active_agents', [])
    if not agents:
        st.info('Waiting for first agent to start...')
        return
    start_time = agents[0]['ts'] if agents else time.time()
    for entry in reversed(agents[-30:]):
        elapsed = entry['ts'] - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        ts_label = f'{minutes:02d}:{seconds:02d}'
        output_hint = ', '.join(entry['output_keys'][:3]) if entry['output_keys'] else ''
        phase_color = {'Planning': '🟦', 'Development': '🟩', 'Integration': '🟧'}.get(entry['phase'], '⬜')
        st.markdown(f"`{ts_label}` {phase_color} {entry['icon']} **{entry['label']}**" + (f'  _{output_hint}_' if output_hint else ''))

def render_communication_log():
    logs = st.session_state.get('communication_log', [])
    if not logs:
        st.caption('No communications yet.')
        return
    for entry in reversed(logs[-20:]):
        lines = entry.strip().split('\n')
        header = lines[0] if lines else ''
        st.markdown(header)

def render_workspace_files():
    files = st.session_state.get('workspace_files', {})
    if not files:
        st.caption('No files generated yet.')
        return
    st.caption(f"{len(files)} file(s)")
    for file_path, content in files.items():
        with st.expander(f'📄 {file_path}', expanded=False):
            extension = file_path.rsplit('.', 1)[-1] if '.' in file_path else ''
            language = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'yaml': 'yaml',
                'yml': 'yaml',
                'md': 'markdown',
                'toml': 'toml',
                'sql': 'sql',
            }.get(extension, '')
            st.code(content, language=language or None)

def render_execution_dashboard():
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

    if is_running:
        time.sleep(1)
        st.rerun()
