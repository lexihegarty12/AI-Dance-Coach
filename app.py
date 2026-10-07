"""Main entry point for the Ballet Technique Analysis Platform demo."""

import streamlit as st

from app_state import initialize_account_state
from ui import inject_app_styles, render_footer

st.set_page_config(
    page_title="Ballet Technique Analysis Platform | Practice review",
    page_icon=":material/accessibility_new:",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_account_state()
inject_app_styles()

with st.sidebar:
    st.markdown('<div class="brand-mark">barre</div><div class="brand-rule"></div>', unsafe_allow_html=True)
    st.caption("Practice, measured.")
    st.markdown("**Current lessons**")
    st.caption("Demi-plié · Tendu · Arabesque")
    st.caption("Camera-dependent practice cues — not grades or medical advice")
    if getattr(st.user, "is_logged_in", False):
        st.caption("Signed-in account")
    else:
        st.caption("Local demo account · session only")

page = st.navigation(
    [
        st.Page("app_pages/lesson_review.py", title="Lesson review", icon=":material/ondemand_video:"),
        st.Page("app_pages/training_plan.py", title="Training plan", icon=":material/calendar_month:"),
        st.Page("app_pages/progress.py", title="Progress", icon=":material/insights:"),
        st.Page("app_pages/account.py", title="My account", icon=":material/account_circle:"),
    ],
    position="top",
)
page.run()
render_footer()
