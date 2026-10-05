"""Main entry point for the AI Dance Coach demo."""

import streamlit as st

st.set_page_config(
    page_title="AI Dance Coach | Practice review",
    page_icon=":material/accessibility_new:",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("## AI Dance Coach")
    st.caption("Focused feedback for everyday ballet practice")
    st.markdown("**Current lessons**")
    st.caption("Demi-plié in first · Tendu")
    st.caption("Camera-dependent practice cues — not grades or medical advice")

page = st.navigation(
    [
        st.Page("app_pages/lesson_review.py", title="Lesson review", icon=":material/ondemand_video:"),
    ],
    position="top",
)
page.run()
