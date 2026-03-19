import asyncio
import streamlit as st
from devteam.gui.execution import fetch_history_async, get_existing_threads

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
