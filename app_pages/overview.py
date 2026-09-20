import streamlit as st

st.title("AI Dance Coach demo", icon=":material/sports_gymnastics:")
st.markdown("### Arabesque penché feedback")
st.write("This focused demo shows how a future AI dance coach can turn one dynamic arabesque penché clip into a visual, understandable practice review — with feedback placed directly on the movement.")

step_cols = st.columns(3)
steps = [("01", "Record", "Capture one short phrase with your full body in view."), ("02", "Review", "The system tracks pose landmarks and highlights a technique cue."), ("03", "Improve", "Replay the moment, make one adjustment, and try again.")]
for column, (number, title, detail) in zip(step_cols, steps):
    with column:
        with st.container(border=True):
            st.caption(number)
            st.subheader(title)
            st.write(detail)

st.subheader("What you can explore in this demo", icon=":material/explore:")
feature_cols = st.columns(2)
with feature_cols[0]:
    with st.container(border=True):
        st.markdown("### Feedback videos")
        st.write("Watch the arabesque penché overlay with plain-language coaching cues for hip alignment and the fifth-position close.")
        st.page_link("app_pages/lesson_review.py", label="Open lesson review", icon=":material/play_arrow:", width="stretch")
with feature_cols[1]:
    with st.container(border=True):
        st.markdown("### A growing coaching model")
        st.write("See how expert annotations, self-recorded clips, and dancer feedback become the foundation for future custom coaching intelligence.")
        st.page_link("app_pages/roadmap.py", label="See what comes next", icon=":material/arrow_forward:", width="stretch")

st.info("This is a demo, not a finished grading system. Feedback is camera-dependent practice guidance and should be reviewed with an instructor.", icon=":material/info:")
