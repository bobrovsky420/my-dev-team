import time
import streamlit as st

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
        if st.session_state.get('crew_started'):
            st.info('Waiting for the first agent response...')
        else:
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
