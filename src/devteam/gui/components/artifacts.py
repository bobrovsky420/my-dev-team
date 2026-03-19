import streamlit as st

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
                'sql': 'sql'
            }.get(extension, '')
            st.code(content, language=language or None)
