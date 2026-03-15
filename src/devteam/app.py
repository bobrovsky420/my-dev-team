import streamlit as st
import asyncio
import yaml
from pathlib import Path

from devteam.cli import WORKSPACES_DIR, build_crew, parse_spec_from_string, generate_thread_id
from devteam.utils import LLMFactory
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

def get_providers_from_config():
    config_path = Path('config/llms.yaml')
    if not config_path.exists():
        return ['ollama', 'groq', 'openai'] # Safe fallback
    try:
        data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return list(data['providers'].keys())
    except Exception as e: # pylint: disable=broad-exception-caught
        st.error(f"Error reading llms.yaml: {e}")
        return ['ollama', 'groq', 'openai'] # Safe fallback

async def run_new_project_async(project_name: str, requirements: str, provider: str, rpm: int = 0):
    thread_id = generate_thread_id(project_name)
    project_folder = WORKSPACES_DIR / thread_id
    project_folder.mkdir(parents=True, exist_ok=True)
    db_path = project_folder / 'state.db'
    llm_factory = LLMFactory(provider=provider)
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(project_folder, llm_factory, checkpointer, rpm)
        final_state = await crew.execute(
            thread_id=thread_id,
            requirements=requirements
        )
        return final_state, thread_id

def get_existing_threads():
    if not WORKSPACES_DIR.exists():
        return []
    return [d.name for d in WORKSPACES_DIR.iterdir() if d.is_dir()]

async def fetch_history_async(thread_id):
    db_path = WORKSPACES_DIR / thread_id / 'state.db'
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(WORKSPACES_DIR / thread_id, LLMFactory(provider='ollama'), checkpointer)
        return await crew.get_history(thread_id)

st.set_page_config(page_title="My AI Dev Team", page_icon='🚀', layout='wide')
st.title("🤖 My AI Dev Team")

st.sidebar.title("Navigation")
mode = st.sidebar.radio(
    "Choose an action:",
    [
        "🚀 Start New Project",
        "🔄 Resume Project",
        "🕰️ View History"
    ]
)

if mode == "🚀 Start New Project":
    st.header("Start a New Project")
    uploaded_file = st.file_uploader("Upload your project requirements (.txt)", type=['txt'])
    col1, col2 = st.columns(2)
    with col1:
        available_providers = get_providers_from_config()
        provider = st.selectbox("LLM Provider", available_providers)
    with col2:
        rpm = st.number_input("Rate Limit (RPM, 0 = unlimited)", min_value=0, value=0, step=10)
    if uploaded_file and st.button("🚀 Launch AI Team", type='primary'):
        content = uploaded_file.read().decode('utf-8')
        project_name, requirements = parse_spec_from_string(content)
        with st.status(f"🧠 AI Team is building '{project_name}'...", expanded=True) as status:
            st.write(f"**Provider:** {provider.upper()}")
            st.write("Initializing workspace, agents, and sandboxes...")
            st.write("*(Note: This process may take several minutes depending on the complexity of your requirements)*")
            try:
                final_state, thread_id = asyncio.run(run_new_project_async(project_name, requirements, provider, rpm))
                if getattr(final_state, 'abort_requested', False) or (isinstance(final_state, dict) and final_state.get('abort_requested')):
                    status.update(label="❌ Workflow Aborted", state='error')
                    st.error("Workflow was aborted by user or validation failure.")
                elif getattr(final_state, 'success', False) or (isinstance(final_state, dict) and final_state.get('success')):
                    status.update(label="🎉 Project Completed Successfully!", state='complete')
                    st.balloons()
                    st.success(f"Files saved to workspace: `{thread_id}`")
                    report = getattr(final_state, 'final_report', None) or (isinstance(final_state, dict) and final_state.get('final_report'))
                    if report:
                        st.subheader("Final Report")
                        st.markdown(report)
                else:
                    status.update(label="🚨 Release Failed: Integration Bugs", state='warning')
                    bugs = getattr(final_state, 'integration_bugs', []) or (isinstance(final_state, dict) and final_state.get('integration_bugs', []))
                    for bug in bugs:
                        st.warning(f"- {bug}")
            except Exception as e: # pylint: disable=broad-exception-caught
                status.update(label="💥 Fatal Error", state='error')
                st.error(f"An unexpected error occurred: {str(e)}")

elif mode == "🔄 Resume Project":
    st.header("Resume or Inject Feedback")
    threads = get_existing_threads()
    if not threads:
        st.warning("No existing workspaces found. Start a new project first!")
    else:
        selected_thread = st.selectbox("Select Project Workspace", threads)
        st.subheader("Time Travel & Intervention")
        feedback = st.text_area("Human Feedback (Optional)", placeholder="e.g., 'Stop using SQLite and use PostgreSQL instead.'")
        col1, col2 = st.columns(2)
        with col1:
            as_node = st.selectbox("Impersonate Agent", ['reviewer', 'qa', 'pm', 'architect'])
        with col2:
            checkpoint = st.text_input("Target Checkpoint ID (Optional)", placeholder="Leave blank for latest state")
        if st.button("🔄 Resume Execution", type='primary'):
            st.success(f"Resuming `{selected_thread}`...")
            if feedback:
                st.warning(f"Injecting feedback as **{as_node.upper()}** into the graph.")

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
                except Exception as e:
                    st.error(f"Failed to read database: {str(e)}")
