"""Main entry point for the AI Dance Coach demo."""

import streamlit as st

st.set_page_config(
    page_title="AI Dance Coach Demo",
    page_icon=":material/accessibility_new:",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("## :material/accessibility_new: AI Dance Coach — Demo")
    st.caption("Arabesque penché feedback demo")
    st.markdown("### Lesson")
    st.caption("Arabesque penché")
    st.caption("Prototype • camera-dependent practice cues")

page = st.navigation(
    [
        st.Page("app_pages/lesson_review.py", title="Lesson review", icon=":material/ondemand_video:"),
    ],
    position="top",
)
page.run()
