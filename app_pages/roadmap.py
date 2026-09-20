import streamlit as st

st.title("What comes next", icon=":material/route:")
st.write("The current demo is the first layer of a larger coaching workflow. Each stage makes the eventual product more specific without pretending that a camera can replace a teacher.")

stages = [("Now", "Pose landmarks", "MediaPipe detects body landmarks and the demo turns them into visible practice cues."), ("Next", "Self-recorded clips", "More clips of the same dancer create a small, consistent dataset of movement attempts and corrections."), ("Later", "Custom coaching model", "Expert annotations can train a separate dance-technique model that learns which landmark patterns map to useful feedback.")]
for label, title, detail in stages:
    with st.container(border=True):
        st.caption(label)
        st.subheader(title)
        st.write(detail)

st.subheader("What makes the data useful", icon=":material/dataset:")
st.markdown("- Timestamped corrections, such as keeping the working hip down.\n- Multiple attempts: comfortable, improving, and intentionally imperfect.\n- Consistent filenames and movement labels.\n- Notes about camera angle, lighting, and confidence.\n- Dancer-level train/test splits so the model is tested fairly.")

st.subheader("Responsible by design", icon=":material/shield:")
st.write("Start with self-recorded clips, keep raw video local, store only the labels and pose data needed for development, and ask permission before using anyone else's video or showing it publicly.")
st.page_link("app_pages/lesson_review.py", label="Return to lesson review", icon=":material/arrow_back:", width="content")
