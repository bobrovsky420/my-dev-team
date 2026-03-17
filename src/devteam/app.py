import streamlit as st
import asyncio
import logging
import time
import yaml
import threading
from queue import Queue, Empty
from pathlib import Path
import aiosqlite
from devteam.cli import WORKSPACES_DIR, build_crew, parse_spec_from_string, generate_thread_id, setup_logging
from devteam.utils import LLMFactory
from devteam.extensions import WorkspaceSaver, StreamlitLogger
from devteam.extensions.streamlit_logger import EVT_START, EVT_STEP, EVT_PAUSE, EVT_FINISH, EVT_ERROR
from devteam import settings
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# ── Setup file logging (no console — Streamlit is a separate process) ──────
setup_logging(console_level=None)

# ── Node metadata for display ──────────────────────────────────────────────
AGENT_META = {
    'pm':        {'icon': '📋', 'label': 'Product Manager',    'phase': 'Planning'},
    'architect': {'icon': '🏗️', 'label': 'System Architect',   'phase': 'Planning'},
    'human':     {'icon': '👤', 'label': 'Human Input',         'phase': 'Planning'},
    'developer': {'icon': '💻', 'label': 'Senior Developer',    'phase': 'Development'},
    'reviewer':  {'icon': '🔍', 'label': 'Code Reviewer',       'phase': 'Development'},
    'qa':        {'icon': '🧪', 'label': 'QA Engineer',         'phase': 'Development'},
    'task_router': {'icon': '🔀', 'label': 'Task Router',       'phase': 'Development'},
    'reporter':  {'icon': '📝', 'label': 'Reporter',            'phase': 'Integration'},
    'final_qa':  {'icon': '✅', 'label': 'Final QA',            'phase': 'Integration'},
}

PHASE_ORDER = ['Planning', 'Development', 'Integration', 'Complete']
PHASE_ICONS = {'Planning': '📋', 'Development': '💻', 'Integration': '📦', 'Complete': '🎉'}


def get_providers_from_config():
    config_path = Path('config/llms.yaml')
    if not config_path.exists():
        return ['ollama', 'groq', 'openai']
    try:
        data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return list(data['providers'].keys())
    except Exception:  # pylint: disable=broad-exception-caught
        return ['ollama', 'groq', 'openai']


# ── Async execution helpers ─────────────────────────────────────────────────
def _run_crew_in_thread(project_name, requirements, provider, rpm, event_queue, result_holder):
    """Run the async crew execution inside a dedicated thread with its own event loop."""
    async def _inner():
        thread_id = generate_thread_id(project_name)
        project_folder = WORKSPACES_DIR / thread_id
        project_folder.mkdir(parents=True, exist_ok=True)
        db_path = project_folder / 'state.db'
        llm_factory = LLMFactory(provider=provider)
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            extensions = [
                WorkspaceSaver(workspace_dir=project_folder),
                StreamlitLogger(event_queue),
            ]
            crew = build_crew(llm_factory, checkpointer, rpm, extensions=extensions)
            final_state = await crew.execute(thread_id=thread_id, requirements=requirements)
            result_holder['final_state'] = final_state
            result_holder['thread_id'] = thread_id

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_inner())
    except Exception as exc:
        result_holder['error'] = str(exc)
    finally:
        loop.close()


def _init_session_state():
    """Ensure all required session-state keys exist."""
    defaults = {
        'execution_active': False,
        'events': [],
        'current_phase': None,
        'active_agents': [],
        'task_progress': {'current': 0, 'total': 0, 'name': ''},
        'communication_log': [],
        'workspace_files': {},
        'specs': '',
        'final_report': '',
        'result_holder': {},
        'event_queue': None,
        'worker_thread': None,
        'revision_count': 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _drain_queue():
    """Pull all available events from queue and process them."""
    q = st.session_state.get('event_queue')
    if q is None:
        return False

    had_events = False
    while True:
        try:
            evt = q.get_nowait()
            had_events = True
            _process_event(evt)
        except Empty:
            break
    if had_events:
        logging.debug("Drained %d total events from queue", len(st.session_state.get('events', [])))
    return had_events


def _process_event(evt):
    """Process a single event and update session state."""
    st.session_state['events'].append(evt)
    etype = evt['type']

    if etype == EVT_START:
        st.session_state['current_phase'] = 'Planning'

    elif etype == EVT_STEP:
        state_update = evt.get('state_update', {})
        full_state = evt.get('full_state', {})

        # Track active agent
        for node_name, node_output in state_update.items():
            meta = AGENT_META.get(node_name, {'icon': '⚙️', 'label': node_name, 'phase': 'Unknown'})
            st.session_state['current_phase'] = meta['phase']
            st.session_state['active_agents'].append({
                'node': node_name,
                'label': meta['label'],
                'icon': meta['icon'],
                'phase': meta['phase'],
                'ts': evt['ts'],
                'output_keys': list(node_output.keys()) if isinstance(node_output, dict) else [],
            })

            # Extract meaningful state updates
            if isinstance(node_output, dict):
                if 'specs' in node_output and node_output['specs']:
                    st.session_state['specs'] = node_output['specs']
                if 'workspace_files' in node_output and node_output['workspace_files']:
                    st.session_state['workspace_files'] = node_output['workspace_files']
                if 'final_report' in node_output and node_output['final_report']:
                    st.session_state['final_report'] = node_output['final_report']
                if 'revision_count' in node_output:
                    st.session_state['revision_count'] = node_output['revision_count']

        # Task progress from full_state
        pending = full_state.get('pending_tasks', [])
        idx = full_state.get('current_task_index', 0)
        current_task = full_state.get('current_task', '')
        if pending:
            task_name = ''
            if idx > 0 and idx <= len(pending):
                task_name = pending[idx - 1].get('task_name', f'Task {idx}')
            st.session_state['task_progress'] = {
                'current': idx,
                'total': len(pending),
                'name': task_name,
            }
        if current_task == 'ALL_DONE':
            st.session_state['current_phase'] = 'Integration'

        # Communication log
        logs = full_state.get('communication_log', [])
        st.session_state['communication_log'] = logs

    elif etype == EVT_PAUSE:
        pass  # Could handle HITL in the future

    elif etype in (EVT_FINISH, EVT_ERROR):
        st.session_state['execution_active'] = False
        if etype == EVT_FINISH:
            st.session_state['current_phase'] = 'Complete'
            final = evt.get('state', {})
            if final.get('final_report'):
                st.session_state['final_report'] = final['final_report']


# ── History fetch ────────────────────────────────────────────────────────────
def get_existing_threads():
    if not WORKSPACES_DIR.exists():
        return []
    return [d.name for d in WORKSPACES_DIR.iterdir() if d.is_dir()]


async def fetch_history_async(thread_id):
    db_path = WORKSPACES_DIR / thread_id / 'state.db'
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(LLMFactory(provider='ollama'), checkpointer)
        return await crew.get_history(thread_id)


# ── Rendering helpers ────────────────────────────────────────────────────────
def _render_phase_tracker():
    """Top-level phase progress indicator."""
    current = st.session_state.get('current_phase')
    cols = st.columns(len(PHASE_ORDER))
    for i, phase in enumerate(PHASE_ORDER):
        with cols[i]:
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


def _render_task_progress():
    """Current task progress bar."""
    tp = st.session_state['task_progress']
    if tp['total'] > 0:
        st.markdown(f"**Current Task:** {tp['name']}  ({tp['current']}/{tp['total']})")
        st.progress(tp['current'] / tp['total'])
    rev = st.session_state.get('revision_count', 0)
    if rev > 0:
        st.caption(f"Revision #{rev}")


def _render_agent_timeline():
    """Activity timeline of agent steps."""
    agents = st.session_state.get('active_agents', [])
    if not agents:
        st.info("Waiting for first agent to start...")
        return

    start_time = agents[0]['ts'] if agents else time.time()
    for entry in reversed(agents[-30:]):  # Show last 30 entries
        elapsed = entry['ts'] - start_time
        mins, secs = divmod(int(elapsed), 60)
        ts_label = f"{mins:02d}:{secs:02d}"
        output_hint = ', '.join(entry['output_keys'][:3]) if entry['output_keys'] else ''
        phase_color = {
            'Planning': '🟦', 'Development': '🟩', 'Integration': '🟧',
        }.get(entry['phase'], '⬜')
        st.markdown(
            f"`{ts_label}` {phase_color} {entry['icon']} **{entry['label']}**"
            + (f"  _{output_hint}_" if output_hint else "")
        )


def _render_communication_log():
    """Show the communication log entries."""
    logs = st.session_state.get('communication_log', [])
    if not logs:
        st.caption("No communications yet.")
        return
    for entry in reversed(logs[-20:]):
        lines = entry.strip().split('\n')
        header = lines[0] if lines else ''
        st.markdown(header)


def _render_workspace_files():
    """File browser for generated workspace files."""
    files = st.session_state.get('workspace_files', {})
    if not files:
        st.caption("No files generated yet.")
        return
    st.caption(f"{len(files)} file(s)")
    for fpath, content in files.items():
        with st.expander(f"📄 {fpath}", expanded=False):
            ext = fpath.rsplit('.', 1)[-1] if '.' in fpath else ''
            lang = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'html': 'html',
                    'css': 'css', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
                    'md': 'markdown', 'toml': 'toml', 'sql': 'sql'}.get(ext, '')
            st.code(content, language=lang or None)


def _render_execution_dashboard():
    """Main dashboard shown during/after crew execution."""
    _render_phase_tracker()
    st.divider()

    # Check if the thread is done
    result = st.session_state.get('result_holder', {})
    is_running = st.session_state.get('execution_active', False)

    # Layout: left side for timeline, right for details
    left, right = st.columns([2, 3])

    with left:
        st.subheader("Agent Activity")
        _render_agent_timeline()

        st.subheader("Task Progress")
        _render_task_progress()

    with right:
        tab_log, tab_files, tab_specs, tab_report = st.tabs([
            "💬 Communication Log", "📁 Workspace Files", "📋 Specs", "📝 Final Report"
        ])
        with tab_log:
            _render_communication_log()
        with tab_files:
            _render_workspace_files()
        with tab_specs:
            specs = st.session_state.get('specs', '')
            if specs:
                st.markdown(specs)
            else:
                st.caption("Specs not yet generated.")
        with tab_report:
            report = st.session_state.get('final_report', '')
            if report:
                st.markdown(report)
            else:
                st.caption("Report not yet available.")

    # Final status banner
    if not is_running and result:
        st.divider()
        if 'error' in result:
            st.error(f"💥 Execution failed: {result['error']}")
        elif 'final_state' in result:
            fs = result['final_state']
            if getattr(fs, 'abort_requested', False):
                st.error("❌ Workflow was aborted.")
            elif getattr(fs, 'success', False):
                st.success(f"🎉 Project completed successfully! Workspace: `{result.get('thread_id', '')}`")
                st.balloons()
            else:
                st.warning("🚨 Release failed — integration bugs found.")
                for bug in getattr(fs, 'integration_bugs', []):
                    st.warning(f"- {bug}")

    # Auto-refresh while running
    if is_running:
        time.sleep(1)
        st.rerun()


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="My AI Dev Team", page_icon='🚀', layout='wide')
_init_session_state()

st.title("🤖 My AI Dev Team")

st.sidebar.title("Navigation")

# Auto-switch to dashboard when execution starts
if st.session_state.get('execution_active') and st.session_state.get('nav_mode') != "📊 Execution Dashboard":
    st.session_state['nav_mode'] = "📊 Execution Dashboard"
    st.rerun()

mode = st.sidebar.radio(
    "Choose an action:",
    [
        "🚀 Start New Project",
        "📊 Execution Dashboard",
        "🔄 Resume Project",
        "🕰️ View History",
    ],
    key='nav_mode',
)

# Drain events on every page load when execution is active
if st.session_state.get('execution_active') or st.session_state.get('event_queue') is not None:
    _drain_queue()
    worker = st.session_state.get('worker_thread')
    if worker and not worker.is_alive():
        _drain_queue()  # Final drain after worker finished
        st.session_state['execution_active'] = False

# ── Start New Project ────────────────────────────────────────────────────────
if mode == "🚀 Start New Project":
    st.header("Start a New Project")

    uploaded_file = st.file_uploader("Upload your project requirements (.txt)", type=['txt'])
    col1, col2 = st.columns(2)
    with col1:
        available_providers = get_providers_from_config()
        provider = st.selectbox("LLM Provider", available_providers)
    with col2:
        rpm = st.number_input("Rate Limit (RPM, 0 = unlimited)", min_value=0, value=0, step=10)
    timeout = st.number_input("LLM Timeout (seconds)", min_value=10, value=120, step=10)

    if uploaded_file and st.button("🚀 Launch AI Team", type='primary'):
        content = uploaded_file.read().decode('utf-8')
        project_name, requirements = parse_spec_from_string(content)

        settings.set_llm_timeout(timeout)

        # Reset session state for new execution
        for k in ['events', 'active_agents', 'communication_log', 'workspace_files',
                   'specs', 'final_report', 'result_holder']:
            st.session_state[k] = [] if k in ('events', 'active_agents', 'communication_log') else (
                {} if k in ('workspace_files', 'result_holder') else ''
            )
        st.session_state['task_progress'] = {'current': 0, 'total': 0, 'name': ''}
        st.session_state['revision_count'] = 0
        st.session_state['current_phase'] = 'Planning'
        st.session_state['execution_active'] = True

        event_queue = Queue()
        st.session_state['event_queue'] = event_queue
        result_holder = {}
        st.session_state['result_holder'] = result_holder

        worker = threading.Thread(
            target=_run_crew_in_thread,
            args=(project_name, requirements, provider, rpm, event_queue, result_holder),
            daemon=True,
        )
        st.session_state['worker_thread'] = worker
        worker.start()

        st.toast(f"🚀 AI Team launched for '{project_name}'!", icon='🤖')
        time.sleep(0.5)
        st.rerun()

# ── Execution Dashboard ─────────────────────────────────────────────────────
elif mode == "📊 Execution Dashboard":
    st.header("Execution Dashboard")

    if st.session_state.get('execution_active') or st.session_state.get('active_agents'):
        _render_execution_dashboard()
    else:
        st.info(
            "No execution in progress. Go to **🚀 Start New Project** to launch one, "
            "or results from a previous run will appear here."
        )

# ── Resume Project ───────────────────────────────────────────────────────────
elif mode == "🔄 Resume Project":
    st.header("Resume or Inject Feedback")
    threads = get_existing_threads()
    if not threads:
        st.warning("No existing workspaces found. Start a new project first!")
    else:
        selected_thread = st.selectbox("Select Project Workspace", threads)
        st.subheader("Time Travel & Intervention")
        feedback = st.text_area("Human Feedback (Optional)",
                                placeholder="e.g., 'Stop using SQLite and use PostgreSQL instead.'")
        col1, col2 = st.columns(2)
        with col1:
            as_node = st.selectbox("Impersonate Agent", ['reviewer', 'qa', 'pm', 'architect'])
        with col2:
            checkpoint = st.text_input("Target Checkpoint ID (Optional)",
                                       placeholder="Leave blank for latest state")
        if st.button("🔄 Resume Execution", type='primary'):
            st.success(f"Resuming `{selected_thread}`...")
            if feedback:
                st.warning(f"Injecting feedback as **{as_node.upper()}** into the graph.")

# ── View History ─────────────────────────────────────────────────────────────
elif mode == "🕰️ View History":
    st.header("Timeline & Checkpoints")
    threads = get_existing_threads()
    if not threads:
        st.warning("No existing workspaces found.")
    else:
        selected_thread = st.selectbox("Select Project Workspace", threads, key='history_thread')
        if st.button("Fetch History"):
            with st.spinner("Digging through SQLite..."):
                try:
                    history_data = asyncio.run(fetch_history_async(selected_thread))
                    if not history_data:
                        st.info("No history found for this thread.")
                    else:
                        st.success(f"Found {len(history_data)} checkpoints!")
                        st.dataframe(
                            history_data,
                            column_config={
                                "time": st.column_config.DatetimeColumn("Timestamp", format='h:mm:ss a'),
                                "ns": "Namespace / Subgraph",
                                "c_id": "Checkpoint ID",
                                "node": "Next Node"
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                except Exception as e: # pylint: disable=broad-exception-caught
                    st.error(f"Failed to read database: {str(e)}")
