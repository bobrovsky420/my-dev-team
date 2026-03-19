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
                    unsafe_allow_html=True
                )
            elif PHASE_ORDER.index(phase) < PHASE_ORDER.index(current or PHASE_ORDER[0]):
                st.markdown(
                    f"<div style='text-align:center;padding:8px;background:#2e7d32;color:white;"
                    f"border-radius:8px'>{icon} {phase} ✓</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align:center;padding:8px;background:#333;color:#888;"
                    f"border-radius:8px'>{icon} {phase}</div>",
                    unsafe_allow_html=True
                )
