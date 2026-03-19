import streamlit as st

def render_welcome_page():
    st.header('Welcome')
    st.markdown(
        'Build software with your AI team from one place. '
        'Launch new work, monitor execution live, or resume an existing workspace.'
    )

    card_1, card_2, card_3 = st.columns(3)
    with card_1:
        st.markdown('### 🚀 Start New')
        st.caption('Upload a requirements file and launch the team.')
        if st.button('Go to New Project', key='welcome_new_project'):
            st.session_state['nav_mode'] = '🚀 Start New Project'
            st.rerun()
    with card_2:
        st.markdown('### 📊 Dashboard')
        st.caption('Track current phase, agent activity, and generated files.')
        if st.button('Open Dashboard', key='welcome_dashboard'):
            st.session_state['nav_mode'] = '📊 Execution Dashboard'
            st.rerun()
    with card_3:
        st.markdown('### 🔄 Resume Work')
        st.caption('Continue from a saved workspace and inject feedback.')
        if st.button('Resume Project', key='welcome_resume'):
            st.session_state['nav_mode'] = '🔄 Resume Project'
            st.rerun()

    st.divider()
    st.subheader('How It Works')
    st.markdown(
        '1. Upload a project requirements `.txt` file.\n'
        '2. Pick provider, rate limit, and timeout settings.\n'
        '3. Launch and watch planning, development, and integration in real time.\n'
        '4. Review the final report and generated workspace files.'
    )
