import pandas as pd
import streamlit as st

from app_core import LESSONS, load_coaching_annotations, load_technique_data, result_paths

st.title("Arabesque penché demo", icon=":material/ondemand_video:")
st.write("Review the arabesque penché feedback-video output and the technique cues this demo is testing.")

selected_lesson = "Arabesque penché"
lesson = LESSONS[selected_lesson]
paths = result_paths(lesson["slug"])
technique = load_technique_data(paths["technique"])
annotations = load_coaching_annotations(lesson["slug"])

st.markdown(f"**{selected_lesson}**  ·  {lesson['level']}  ·  {lesson['duration']}\n\n{lesson['description']}")
if not paths["feedback"].exists():
    st.error("The rendered feedback video is not available for this lesson yet.", icon=":material/error:")
    st.stop()

video_col, cue_col = st.columns([1.55, 1], gap="large")
with video_col:
    with st.container(border=True):
        st.subheader("Feedback video", icon=":material/ondemand_video:")
        st.video(str(paths["feedback"]))
        if lesson.get("analysis") == "hip_alignment":
            st.caption("Green shows the supporting hip-to-foot alignment cue; red marks a specific coaching moment.")
        else:
            st.caption("Green means the cue is within the alert range; red means pause and reset.")

with cue_col:
    with st.container(border=True):
        st.subheader("Today's coaching cue", icon=":material/lightbulb:")
        st.markdown(f"### {lesson['focus']}")
        detail = "As you bend, keep the front of the ribs stacked above the pelvis." if lesson.get("analysis") != "hip_alignment" else "As the back leg lengthens, keep the working hip down and finish the close to fifth position."
        st.write(f"{detail} Use the on-screen cue as a practice reminder—not as a grade.")
        if annotations:
            lines = [f"- **0:{int(item['start_seconds']):02d}–0:{int(item['end_seconds']):02d}** — {item['label']}." for item in annotations]
            st.markdown("**Key moments**\n\n" + "\n".join(lines))
        st.success("Try one slower repetition, then replay the feedback.", icon=":material/replay:")

    if paths["annotated"].exists():
        with st.container(border=True):
            st.subheader("What the coach tracks", icon=":material/visibility:")
            st.image(str(paths["annotated"]), width="stretch")
            st.caption("Pose landmarks and the alignment line used for this practice cue.")

st.subheader("A quick read of this repetition", icon=":material/query_stats:")
if technique is not None and not technique.empty:
    usable_count = len(technique)
    total_count = len(pd.read_csv(paths["technique"]))
    metric_cols = st.columns(3)
    metric_cols[0].metric("Usable frames", f"{usable_count}/{total_count}")
    metric_column = "supporting_hip_offset_ratio" if "supporting_hip_offset_ratio" in technique.columns else "torso_lean_degrees"
    if metric_column == "supporting_hip_offset_ratio":
        metric_cols[1].metric("Average hip offset", f"{technique[metric_column].mean():.2f}")
        metric_cols[2].metric("Peak hip offset", f"{technique[metric_column].max():.2f}")
        st.line_chart(technique.set_index("timestamp_seconds")[metric_column], y_label="Hip-to-foot offset ratio", x_label="Time (seconds)")
    else:
        metric_cols[1].metric("Average torso lean", f"{technique[metric_column].mean():.1f}°")
        metric_cols[2].metric("Peak torso lean", f"{technique[metric_column].max():.1f}°")
        st.line_chart(technique.set_index("timestamp_seconds")[metric_column], y_label="Torso lean (degrees)", x_label="Time (seconds)")
else:
    st.info("Technique measurements are not available for this lesson yet.", icon=":material/info:")

with st.expander("How to use this feedback", icon=":material/help:"):
    st.markdown("- Pause when the red cue appears.\n- Make one small adjustment, then try the phrase again.\n- Keep the camera angle and distance consistent between attempts.\n\nThis is a camera-dependent practice aid, not a ballet grade, diagnosis, or replacement for an instructor.")
