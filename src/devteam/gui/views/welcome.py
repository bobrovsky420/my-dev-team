import streamlit as st

def render_welcome_page():
    st.header('Welcome')
    st.markdown(
        'Build software with your AI team from one place. '
        'Launch new work, monitor execution live, or resume an existing workspace.'
    )

    def navigate_to(mode: str):
        st.session_state['requested_mode'] = mode

    card_1, card_2, card_3 = st.columns(3)
    with card_1:
        st.markdown('### 🚀 Start New')
        st.caption('Upload a requirements file and launch the team.')
        st.button('Go to New Project', key='welcome_new_project', on_click=navigate_to, args=('🚀 Start New Project',))
    with card_2:
        st.markdown('### 📊 Dashboard')
        st.caption('Track current phase, agent activity, and generated files.')
        st.button('Open Dashboard', key='welcome_dashboard', on_click=navigate_to, args=('📊 Execution Dashboard',))
    with card_3:
        st.markdown('### 🔄 Resume Work')
        st.caption('Continue from a saved workspace and inject feedback.')
        st.button('Resume Project', key='welcome_resume', on_click=navigate_to, args=('🔄 Resume Project',))

    st.divider()
    st.subheader('How It Works')
    st.markdown(
        '1. Upload a project requirements `.txt` file.\n'
        '2. Pick provider, rate limit, and timeout settings.\n'
        '3. Launch and watch planning, development, and integration in real time.\n'
        '4. Review the final report and generated workspace files.'
    )
