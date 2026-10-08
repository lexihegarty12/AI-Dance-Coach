import streamlit as st

from app_core import CORRECTION_PATHWAYS, recommend_tiktok_clips


st.title("Personalized training plan")
st.write(
    "Turn one technique correction into a focused practice week. Choose the correction that best matches your latest review, then adjust the plan to fit your practice time."
)

with st.form("training_plan_form"):
    correction_name = st.selectbox("What would you like to improve?", list(CORRECTION_PATHWAYS))
    level = st.selectbox("Current level", ["Foundational", "Developing", "Intermediate"])
    practice_days = st.slider("Practice days this week", min_value=2, max_value=7, value=4)
    minutes = st.segmented_control("Time per session", ["10 minutes", "20 minutes", "30 minutes"], default="20 minutes")
    practice_stage = st.selectbox(
        "Where are you with this correction?",
        ["First time with this cue", "Still inconsistent", "Ready to integrate"],
        help="This changes which drills and practice emphasis appear first.",
    )
    submitted = st.form_submit_button("Build my plan", type="primary")

if "training_plan_submitted" not in st.session_state:
    st.session_state.training_plan_submitted = False
if submitted:
    st.session_state.training_plan_submitted = True
    st.session_state.training_plan_correction = correction_name
    st.session_state.training_plan_level = level
    st.session_state.training_plan_days = practice_days
    st.session_state.training_plan_minutes = minutes or "20 minutes"
    st.session_state.training_plan_stage = practice_stage

if not st.session_state.training_plan_submitted:
    with st.container(border=True):
        st.subheader("Start with a correction")
        st.write("Your plan is built around one clear cue at a time. You can connect this selection directly to the analysis result in a later version.")
    st.stop()

selected_name = st.session_state.training_plan_correction
pathway = CORRECTION_PATHWAYS[selected_name]
days = st.session_state.training_plan_days
minutes = st.session_state.training_plan_minutes
practice_stage = st.session_state.get("training_plan_stage", "First time with this cue")

with st.container(border=True):
    st.caption(f"{st.session_state.training_plan_level} · {pathway['positions']} · {days} practice days · {minutes}")
    st.subheader(selected_name)
    st.write(pathway["summary"])
    st.info(f"Practice cue: {pathway['cue']}")
    st.caption(f"Personalized for: {practice_stage.lower()}")

tiktok_clips = recommend_tiktok_clips(selected_name, st.session_state.training_plan_level, practice_stage)
with st.container(border=True):
    st.subheader("Recommended TikTok tips")
    st.caption("Optional coaching examples matched to this correction. These do not affect your analysis or score.")
    if not tiktok_clips:
        st.info("Teacher-reviewed TikTok tips will appear here as the recommendation library is added.")
    else:
        for clip in tiktok_clips:
            st.markdown(f"**{clip.get('title', 'Technique tip')}** · {clip.get('creator', 'TikTok creator')}")
            if clip.get("takeaway"):
                st.write(clip["takeaway"])
            st.link_button("Watch on TikTok", str(clip["url"]), width="content")

st.subheader("Your weekly structure")
schedule = [
    ("Day 1", "Learn the pathway", pathway["exercises"][0]),
    ("Day 2", "Build control", pathway["exercises"][1]),
    ("Day 3", "Combine and repeat", pathway["exercises"][2]),
    ("Day 4", "Review and record", pathway["exercises"][0]),
    ("Day 5", "Small focused practice", pathway["exercises"][1]),
    ("Day 6", "Full correction check", pathway["exercises"][2]),
    ("Day 7", "Rest or gentle review", pathway["exercises"][0]),
]

for day, focus, exercise in schedule[:days]:
    with st.container(border=True):
        st.markdown(f"**{day} · {focus}**")
        st.write(f"{exercise[0]} · {exercise[1]}")
        st.caption(exercise[2])

with st.container(border=True):
    st.subheader("After your practice week")
    st.write("Record the same movement from the same camera angle and return to Lesson review. Compare one correction at a time instead of trying to change everything at once.")
    st.caption("Use **Lesson review** in the navigation above when you are ready to record your next attempt.")

st.warning("This plan is practice guidance, not a medical assessment or a replacement for an in-person teacher. Stop if you feel pain.")
