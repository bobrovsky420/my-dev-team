import streamlit as st
from devteam.gui.rendering import render_execution_dashboard

def render_execution_dashboard_page():
    st.header('Execution Dashboard')
    if st.session_state.get('execution_active') or st.session_state.get('active_agents'):
        render_execution_dashboard()
    else:
        st.info(
            'No execution in progress. Go to **🚀 Start New Project** to launch one, '
            'or results from a previous run will appear here.'
        )
