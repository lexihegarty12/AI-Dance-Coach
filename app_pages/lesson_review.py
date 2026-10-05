import base64
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from app_core import LESSONS, load_technique_data

try:
    import cv2
except ModuleNotFoundError:
    cv2 = None


BACKGROUND_PATH = Path(__file__).resolve().parents[1] / "assets" / "ballet_studio_barre_background.png"
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_UPLOAD_SECONDS = 60


def video_metadata(video_bytes: bytes, filename: str) -> tuple[float, int, int] | None:
    """Return duration, width, and height for an uploaded clip."""
    if cv2 is None:
        return None
    suffix = Path(filename).suffix.lower() or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix) as temporary_file:
        temporary_file.write(video_bytes)
        temporary_file.flush()
        capture = cv2.VideoCapture(temporary_file.name)
        if not capture.isOpened():
            return None
        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frames = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        capture.release()
    duration = frames / fps if fps else 0
    return duration, width, height


def fallback_uploaded_video(video_bytes: bytes, filename: str, prefix: str) -> dict[str, str]:
    """Keep the hosted app usable when optional computer vision packages are unavailable."""
    work_dir = Path(tempfile.mkdtemp(prefix=prefix))
    suffix = Path(filename).suffix.lower() or ".mp4"
    input_path = work_dir / f"uploaded_video{suffix}"
    input_path.write_bytes(video_bytes)
    return {
        "input": str(input_path),
        "feedback": str(input_path),
        "annotated": str(work_dir / "annotated_sample.jpg"),
        "technique": str(work_dir / "technique_results.csv"),
        "fallback": "true",
    }


@st.cache_data(show_spinner=False, max_entries=4)
def process_uploaded_video(video_bytes: bytes, filename: str, camera_view: str) -> dict[str, str]:
    """Analyze and render one uploaded demi-plié clip."""
    if cv2 is None:
        return fallback_uploaded_video(video_bytes, filename, "dance_coach_preview_")
    try:
        from src.analyze_technique import analyze_video
        from src.render_feedback_video import render
    except ModuleNotFoundError:
        return fallback_uploaded_video(video_bytes, filename, "dance_coach_preview_")
    work_dir = Path(tempfile.mkdtemp(prefix="dance_coach_"))
    suffix = Path(filename).suffix.lower() or ".mp4"
    input_path = work_dir / f"uploaded_video{suffix}"
    results_dir = work_dir / "results"
    input_path.write_bytes(video_bytes)
    technique_path, annotated_path = analyze_video(input_path, results_dir, frame_stride=2)
    feedback_path = render(
        input_path,
        results_dir,
        threshold=10 if camera_view == "Side" else 0.35,
        analysis="plie_side" if camera_view == "Side" else "plie",
        annotations_path=work_dir / "no_annotations.json",
        frame_stride=2,
    )
    return {
        "input": str(input_path),
        "feedback": str(feedback_path),
        "annotated": str(annotated_path),
        "technique": str(technique_path),
    }


@st.cache_data(show_spinner=False, max_entries=4)
def process_uploaded_tendu(video_bytes: bytes, filename: str, camera_view: str) -> dict[str, str]:
    """Analyze and render one uploaded front-view tendu clip."""
    if cv2 is None:
        return fallback_uploaded_video(video_bytes, filename, "dance_coach_tendu_preview_")
    try:
        from src.analyze_turnout_proxy import analyze as analyze_tendu
        from src.render_feedback_video import render
    except ModuleNotFoundError:
        return fallback_uploaded_video(video_bytes, filename, "dance_coach_tendu_preview_")
    work_dir = Path(tempfile.mkdtemp(prefix="dance_coach_tendu_"))
    suffix = Path(filename).suffix.lower() or ".mp4"
    input_path = work_dir / f"uploaded_video{suffix}"
    results_dir = work_dir / "results"
    input_path.write_bytes(video_bytes)
    technique_path, annotated_path = analyze_tendu(input_path, results_dir, frame_stride=2)
    feedback_path = render(
        input_path,
        results_dir,
        threshold=55 if camera_view == "Side" else 45,
        analysis="tendu",
        annotations_path=work_dir / "no_annotations.json",
        frame_stride=2,
    )
    return {
        "input": str(input_path),
        "feedback": str(feedback_path),
        "annotated": str(annotated_path),
        "technique": str(technique_path),
    }


if BACKGROUND_PATH.exists():
    encoded_background = base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii")
    st.markdown(
        f"""<style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 252, 247, 0.88), rgba(255, 252, 247, 0.92)),
                              url('data:image/png;base64,{encoded_background}');
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>""",
        unsafe_allow_html=True,
    )

st.title("Practice review")
st.write("Upload one short clip, choose the camera angle, and get one focused practice cue.")

selected_lesson = st.selectbox("Choose a lesson", list(LESSONS), index=0)
lesson = LESSONS[selected_lesson]
with st.container(border=True):
    st.markdown(f"**{selected_lesson}**  ·  {lesson['level']}")
    st.write(lesson["description"])

if lesson.get("analysis") in ("plie", "tendu"):
    camera_view = st.selectbox(
        "Camera angle",
        ["Front", "Side"],
        help="Choose the view that matches your recording. The app uses different practice cues for each angle.",
    )
    if camera_view == "Front":
        st.caption("Front view → knee alignment for plié · foot alignment for tendu")
    else:
        st.caption("Side view → posture and depth for plié · foot line for tendu")
    with st.expander("Recording tips", expanded=False):
        st.markdown(
            "- Record one dancer for 5–60 seconds.\n"
            "- Keep the camera stationary and show your full body, including both feet.\n"
            "- Use good lighting and avoid people crossing in front of you.\n"
            "- Choose the angle that matches where your camera is placed."
        )
    uploaded_file = st.file_uploader(
        "Upload a short video",
        type=["mp4", "mov", "m4v"],
        help="Use one dancer, a stationary camera, and keep your full body visible.",
    )
    if uploaded_file is None:
        with st.container(border=True):
            st.subheader("Upload a clip to begin")
            st.write("Your video will be analyzed after you upload it. No example video is loaded.")
            st.caption("Supported formats: MP4, MOV, and M4V · Maximum length: 60 seconds")
        st.stop()

    if uploaded_file is not None:
        video_bytes = uploaded_file.getvalue()
        if len(video_bytes) > MAX_UPLOAD_BYTES:
            st.error("This video is larger than 100 MB. Please upload a shorter clip or compress it first.")
            st.stop()
        metadata = video_metadata(video_bytes, uploaded_file.name)
        if metadata is None and cv2 is not None:
            st.error("We could not read this video. Try exporting it as MP4 or MOV and upload it again.")
            st.stop()
        if metadata is None:
            st.caption("Ready to review · hosted preview mode")
        else:
            duration, width, height = metadata
            if duration <= 0:
                st.error("We could not determine the video duration. Please try another clip.")
                st.stop()
            if duration > MAX_UPLOAD_SECONDS:
                st.error(f"This clip is {duration:.1f} seconds long. Please upload a clip no longer than 60 seconds.")
                st.stop()
            if width < 320 or height < 320:
                st.error("This video is too small to analyze reliably. Please use a higher-resolution recording.")
                st.stop()
            st.caption(f"Ready to analyze · {duration:.1f} seconds · {width}×{height}")
        with st.spinner(f"Analyzing your {selected_lesson.lower()}..."):
            if lesson.get("analysis") == "tendu":
                processed = process_uploaded_tendu(video_bytes, uploaded_file.name, camera_view)
            else:
                processed = process_uploaded_video(video_bytes, uploaded_file.name, camera_view)
        video_path = Path(processed["feedback"])
        annotated_path = Path(processed["annotated"])
        technique_path = Path(processed["technique"])
        hosted_preview = processed.get("fallback") == "true"

technique = load_technique_data(technique_path)
pose_quality = None
if technique is not None and not technique.empty:
    total_frames = len(pd.read_csv(technique_path))
    pose_quality = len(technique) / max(total_frames, 1)

video_col, cue_col = st.columns([1.55, 1], gap="large")
with video_col:
    with st.container(border=True):
        st.subheader("Practice video")
        st.video(str(video_path))
        if lesson.get("analysis") in ("plie", "tendu"):
            cue_name = "knee" if lesson["analysis"] == "plie" and camera_view == "Front" else "posture" if lesson["analysis"] == "plie" else "foot alignment"
            if hosted_preview:
                st.caption(f"Selected angle: {camera_view} view · Practice cue: {cue_name}.")
                st.caption("Hosted preview mode: landmark overlays are unavailable in this runtime.")
            else:
                st.caption(f"Analyzed angle: {camera_view} view · Green lines show the {cue_name} cue.")

with cue_col:
    with st.container(border=True):
        st.subheader("Today's coaching cue")
        feedback_type = "Knee alignment" if lesson["analysis"] == "plie" and camera_view == "Front" else "Posture and depth" if lesson["analysis"] == "plie" else "Foot alignment"
        st.caption(f"{camera_view} view · {feedback_type}")
        if lesson.get("analysis") == "plie" and camera_view == "Side":
            focus_text = "Stay upright and control the depth"
            detail = "From the side, keep your ribs stacked over your hips as you lower and rise smoothly."
        elif lesson.get("analysis") == "plie":
            focus_text = lesson["focus"]
            detail = "As you lower into first position, let the knees travel in the same direction as the toes."
        elif lesson.get("analysis") == "tendu":
            focus_text = lesson["focus"]
            detail = "As the foot reaches away, keep the foot line consistent with the lower leg and finish through the toes."
        elif lesson.get("analysis") == "hip_alignment":
            focus_text = lesson["focus"]
            detail = "As the back leg lengthens, keep the working hip down and finish the close to fifth position."
        else:
            focus_text = lesson["focus"]
            detail = "As you bend, keep the front of the ribs stacked above the pelvis."
        st.markdown(f"### {focus_text}")
        if pose_quality is not None and pose_quality >= 0.75:
            st.success("The clip was clear enough to track your full-body pose.", icon=":material/check_circle:")
        else:
            st.warning("Some frames were difficult to track. Treat this correction as tentative and improve the lighting or camera distance next time.")
        st.write(f"{detail} Use the on-screen cue as a practice reminder—not as a grade.")
        st.success("Try one slower repetition, then replay the clip.", icon=":material/replay:")

    if annotated_path.exists():
        with st.container(border=True):
            st.subheader("What the coach tracks")
            st.image(str(annotated_path), width="stretch")
            st.caption("Pose landmarks and the alignment line used for this practice cue.")

st.subheader("A quick read of this repetition")
if technique is not None and not technique.empty:
    usable_count = len(technique)
    total_count = len(pd.read_csv(technique_path))
    metric_cols = st.columns(3)
    metric_cols[0].metric("Usable frames", f"{usable_count}/{total_count}")
    if lesson.get("analysis") == "plie" and camera_view == "Front":
        left_offset = technique["left_knee_to_toe_offset"].mean()
        right_offset = technique["right_knee_to_toe_offset"].mean()
        torso = technique["torso_lean_degrees"].mean()
        metric_cols[1].metric("Left knee offset", f"{left_offset:.2f}")
        metric_cols[2].metric("Right knee offset", f"{right_offset:.2f}")
        st.line_chart(
            technique.set_index("timestamp_seconds")[[
                "left_knee_to_toe_offset",
                "right_knee_to_toe_offset",
                "torso_lean_degrees",
            ]],
            y_label="Camera-dependent proxy",
            x_label="Time (seconds)",
        )
        st.caption(f"Average torso lean: {torso:.1f}°. Knee offsets above roughly 0.35 are front-view practice cues.")
    elif lesson.get("analysis") == "plie" and camera_view == "Side":
        torso = technique["torso_lean_degrees"].mean()
        depth = technique["plie_depth_angle"].mean()
        metric_cols[1].metric("Average torso lean", f"{torso:.1f}°")
        metric_cols[2].metric("Average knee angle", f"{depth:.1f}°")
        st.line_chart(
            technique.set_index("timestamp_seconds")[["torso_lean_degrees", "plie_depth_angle"]],
            y_label="Side-view proxy",
            x_label="Time (seconds)",
        )
        st.caption("Side-view feedback focuses on staying upright and maintaining a controlled plié depth.")
    elif lesson.get("analysis") == "tendu":
        left_alignment = technique["left_foot_alignment_deviation_degrees"].mean()
        right_alignment = technique["right_foot_alignment_deviation_degrees"].mean()
        metric_cols[1].metric("Left foot deviation", f"{left_alignment:.1f}°")
        metric_cols[2].metric("Right foot deviation", f"{right_alignment:.1f}°")
        st.line_chart(
            technique.set_index("timestamp_seconds")[[
                "left_foot_alignment_deviation_degrees",
                "right_foot_alignment_deviation_degrees",
            ]],
            y_label="Foot alignment deviation",
            x_label="Time (seconds)",
        )
        st.caption("Larger deviation is a camera-dependent cue to check for sickling or winging.")
    elif "supporting_hip_offset_ratio" in technique.columns:
        metric_column = "supporting_hip_offset_ratio"
        metric_cols[1].metric("Average hip offset", f"{technique[metric_column].mean():.2f}")
        metric_cols[2].metric("Peak hip offset", f"{technique[metric_column].max():.2f}")
        st.line_chart(technique.set_index("timestamp_seconds")[metric_column], y_label="Hip-to-foot offset ratio", x_label="Time (seconds)")
    else:
        metric_column = "torso_lean_degrees"
        metric_cols[1].metric("Average torso lean", f"{technique[metric_column].mean():.1f}°")
        metric_cols[2].metric("Peak torso lean", f"{technique[metric_column].max():.1f}°")
        st.line_chart(technique.set_index("timestamp_seconds")[metric_column], y_label="Torso lean (degrees)", x_label="Time (seconds)")
else:
    st.info("Technique measurements are not available for this lesson yet.", icon=":material/info:")

with st.expander("How to use this feedback"):
    st.markdown("- Pause when the red cue appears.\n- Make one small adjustment, then try the phrase again.\n- Keep the camera angle and distance consistent between attempts.\n\nThis is a camera-dependent practice aid, not a ballet grade, diagnosis, or replacement for an instructor.")
