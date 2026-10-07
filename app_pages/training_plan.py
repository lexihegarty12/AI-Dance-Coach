import streamlit as st

from app_core import CORRECTION_PATHWAYS, recommend_video_clips


st.title("Personalized training plan", icon=":material/calendar_month:")
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
        help="This changes which teaching clips and drills appear first.",
    )
    resource_preference = st.segmented_control(
        "Resource preference",
        ["Videos", "Videos and articles"],
        default="Videos",
    )
    submitted = st.form_submit_button("Build my plan", type="primary", icon=":material/auto_awesome:")

if "training_plan_submitted" not in st.session_state:
    st.session_state.training_plan_submitted = False
if submitted:
    st.session_state.training_plan_submitted = True
    st.session_state.training_plan_correction = correction_name
    st.session_state.training_plan_level = level
    st.session_state.training_plan_days = practice_days
    st.session_state.training_plan_minutes = minutes or "20 minutes"
    st.session_state.training_plan_stage = practice_stage
    st.session_state.training_plan_resources = resource_preference or "Videos"

if not st.session_state.training_plan_submitted:
    with st.container(border=True):
        st.subheader("Start with a correction")
        st.write("Your plan is built around one clear cue at a time. You can connect this selection directly to the analysis result in a later version.")
    st.stop()

selected_name = st.session_state.training_plan_correction
pathway = CORRECTION_PATHWAYS[selected_name]
days = st.session_state.training_plan_days
minutes = st.session_state.training_plan_minutes
resource_preference = st.session_state.training_plan_resources
practice_stage = st.session_state.get("training_plan_stage", "First time with this cue")

with st.container(border=True):
    st.caption(f"{st.session_state.training_plan_level} · {pathway['positions']} · {days} practice days · {minutes}")
    st.subheader(selected_name)
    st.write(pathway["summary"])
    st.info(f"Practice cue: {pathway['cue']}", icon=":material/lightbulb:")
    st.caption(f"Personalized for: {practice_stage.lower()}")

st.subheader("Your weekly structure", icon=":material/event:")
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

st.subheader("Teacher video notes", icon=":material/school:")
st.caption("Watch a focused reference clip, then use the annotated teaching points as a short practice checklist. Notes are concise editorial takeaways, not a replacement for the full lesson or an instructor.")

videos = recommend_video_clips(selected_name, st.session_state.training_plan_level, practice_stage, minutes)
if videos:
    carousel_key = f"video_index_{selected_name}"
    if carousel_key not in st.session_state:
        st.session_state[carousel_key] = 0
    video_index = st.session_state[carousel_key] % len(videos)
    video = videos[video_index]

    with st.container(border=True):
        st.markdown(f'<div class="report-kicker">Reference {video_index + 1} of {len(videos)}</div>', unsafe_allow_html=True)
        st.markdown(f"### {video['title']}")
        st.caption(video["channel"])
        st.markdown(
            f'<div class="assessment-note" style="margin:.6rem 0 1rem">Selected for a <strong>{st.session_state.training_plan_level.lower()}</strong> dancer who is <strong>{practice_stage.lower()}</strong>.</div>',
            unsafe_allow_html=True,
        )
        video_col, notes_col = st.columns([1.25, 1], gap="large")
        with video_col:
            st.video(video["url"])
            st.link_button("Open source video", video["source_url"], icon=":material/open_in_new:")
        with notes_col:
            st.markdown("**Annotated takeaways**")
            for label, note in video["annotations"]:
                st.markdown(
                    f'<div class="assessment-note" style="margin-bottom:.65rem"><strong>{label}</strong><br>{note}</div>',
                    unsafe_allow_html=True,
                )

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            previous = st.button("Previous", icon=":material/arrow_back:", key=f"previous_{selected_name}")
            st.caption(f"Clip {video_index + 1} / {len(videos)}")
            next_video = st.button("Next", icon=":material/arrow_forward:", key=f"next_{selected_name}")
        if previous:
            st.session_state[carousel_key] = (video_index - 1) % len(videos)
            st.rerun()
        if next_video:
            st.session_state[carousel_key] = (video_index + 1) % len(videos)
            st.rerun()
else:
    with st.container(border=True):
        st.info("No curated video has been added for this correction yet.", icon=":material/video_library:")

with st.container(border=True):
    st.subheader("After your practice week", icon=":material/replay:")
    st.write("Record the same movement from the same camera angle and return to Lesson review. Compare one correction at a time instead of trying to change everything at once.")
    st.page_link("app_pages/lesson_review.py", label="Open lesson review", icon=":material/ondemand_video:")

st.warning("This plan is practice guidance, not a medical assessment or a replacement for an in-person teacher. Stop if you feel pain.", icon=":material/health_and_safety:")
