import tempfile
import subprocess
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st

from app_core import LESSONS, REFERENCE_BENCHMARK_DIR, load_technique_data, local_reference_videos
from app_state import save_review_session

try:
    import cv2
except (ImportError, ModuleNotFoundError):
    # Hosted environments may have an incompatible optional OpenCV build.
    # The app can still run in preview mode without computer-vision analysis.
    cv2 = None


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_UPLOAD_SECONDS = 60


@st.cache_data(show_spinner=False, max_entries=4)
def make_slow_motion_video(video_path: str) -> str:
    """Create a 0.5x copy of the already-annotated feedback video."""
    source = Path(video_path)
    output = source.with_name(f"{source.stem}_slow.mp4")
    if output.exists():
        return str(output)
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [ffmpeg, "-y", "-i", str(source), "-filter:v", "setpts=2*PTS", "-an", str(output)],
            check=True,
            capture_output=True,
        )
    except (ImportError, OSError, subprocess.CalledProcessError):
        return str(source)
    return str(output)


def key_moments(technique: pd.DataFrame | None) -> dict[str, float]:
    """Return useful seek points from the measured timeline."""
    if technique is None or technique.empty or "timestamp_seconds" not in technique.columns:
        return {"Start": 0.0, "Deepest point": 0.0, "Return": 0.0}
    timestamps = technique["timestamp_seconds"].astype(float)
    start = float(timestamps.min())
    if "plie_depth_angle" in technique.columns:
        index = technique["plie_depth_angle"].idxmin()
    elif "supporting_hip_offset_ratio" in technique.columns:
        index = technique["supporting_hip_offset_ratio"].idxmin()
    else:
        metric = next((column for column in technique.columns if column != "timestamp_seconds"), None)
        index = technique[metric].idxmax() if metric else technique.index[0]
    deepest = float(technique.loc[index, "timestamp_seconds"])
    duration = float(timestamps.max())
    return {"Start": start, "Deepest point": deepest, "Return": max(deepest, min(duration, deepest + max(.5, (duration - deepest) * .45)))}


def session_metric_snapshot(lesson: dict[str, object], camera_view: str, technique: pd.DataFrame | None) -> dict[str, float]:
    """Keep only comparable, human-readable measures for progress tracking."""
    if technique is None or technique.empty:
        return {}
    if lesson.get("analysis") == "plie" and camera_view == "Front":
        return {"knee_offset": float((technique["left_knee_to_toe_offset"].mean() + technique["right_knee_to_toe_offset"].mean()) / 2)}
    if lesson.get("analysis") == "plie" and camera_view == "Side":
        return {"torso_lean_degrees": float(technique["torso_lean_degrees"].mean()), "plie_depth_angle": float(technique["plie_depth_angle"].mean())}
    if lesson.get("analysis") == "tendu":
        return {"foot_deviation_degrees": float((technique["left_foot_alignment_deviation_degrees"].mean() + technique["right_foot_alignment_deviation_degrees"].mean()) / 2)}
    if lesson.get("analysis") == "arabesque" and "supporting_hip_offset_ratio" in technique.columns:
        metrics = {"supporting_hip_offset_ratio": float(technique["supporting_hip_offset_ratio"].mean())}
        for column in ("working_leg_straightness_degrees", "torso_lean_degrees", "shoulder_hip_offset_ratio", "standing_foot_line_degrees"):
            if column in technique.columns:
                metrics[column] = float(technique[column].mean())
        return metrics
    return {}


@st.cache_data(show_spinner=False, max_entries=12)
def load_reference_measurements(slug: str, camera_view: str) -> pd.DataFrame | None:
    """Load persistent reference benchmarks, analyzing each source only once."""
    reference_paths = local_reference_videos(slug, camera_view)
    benchmark_paths = sorted(REFERENCE_BENCHMARK_DIR.glob(f"{slug}_{camera_view.lower()}_*.csv"))
    # Hosted deployments may contain the compact benchmark CSVs but not the
    # original reference videos, which are too large to ship with the app.
    if not reference_paths and benchmark_paths:
        benchmark_frames = [load_technique_data(path) for path in benchmark_paths]
        usable_frames = [frame for frame in benchmark_frames if frame is not None and not frame.empty]
        return pd.concat(usable_frames, ignore_index=True) if usable_frames else None
    if not reference_paths:
        return None
    measurements: list[pd.DataFrame] = []
    REFERENCE_BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    try:
        for reference_index, reference_path in enumerate(reference_paths, start=1):
            benchmark_path = REFERENCE_BENCHMARK_DIR / f"{slug}_{camera_view.lower()}_{reference_index}.csv"
            benchmark_is_current = benchmark_path.exists() and benchmark_path.stat().st_mtime >= reference_path.stat().st_mtime
            if benchmark_is_current:
                reference_data = load_technique_data(benchmark_path)
            else:
                work_dir = Path(tempfile.mkdtemp(prefix="dance_coach_reference_"))
                results_dir = work_dir / "results"
                if slug == "tendu_front_alignment":
                    from src.analyze_turnout_proxy import analyze as analyze_tendu

                    technique_path, _ = analyze_tendu(reference_path, results_dir, frame_stride=2)
                elif slug == "arabesque_reference":
                    from src.analyze_arabesque import analyze_video as analyze_arabesque

                    analyze_arabesque(reference_path, results_dir)
                    technique_path = results_dir / "technique_results.csv"
                else:
                    from src.analyze_technique import analyze_video

                    technique_path, _ = analyze_video(reference_path, results_dir, frame_stride=2)
                shutil.copy2(technique_path, benchmark_path)
                reference_data = load_technique_data(benchmark_path)
            if reference_data is not None and not reference_data.empty:
                measurements.append(reference_data)
    except (ImportError, OSError, RuntimeError, ValueError):
        return None
    return pd.concat(measurements, ignore_index=True) if measurements else None


def compare_with_reference(lesson: dict[str, object], camera_view: str, technique: pd.DataFrame | None) -> dict[str, float] | None:
    """Return user-minus-reference deltas without exposing the reference clips."""
    reference = load_reference_measurements(lesson["slug"], camera_view)
    if reference is None or technique is None or technique.empty:
        return None
    if lesson.get("analysis") == "plie" and camera_view == "Front":
        user_value = (technique["left_knee_to_toe_offset"].mean() + technique["right_knee_to_toe_offset"].mean()) / 2
        reference_value = (reference["left_knee_to_toe_offset"].mean() + reference["right_knee_to_toe_offset"].mean()) / 2
        return {"metric": "average knee offset", "user": float(user_value), "reference": float(reference_value), "difference": float(user_value - reference_value)}
    if lesson.get("analysis") == "plie" and camera_view == "Side":
        user_value = float(technique["torso_lean_degrees"].mean())
        reference_value = float(reference["torso_lean_degrees"].mean())
        return {"metric": "average torso lean", "user": user_value, "reference": reference_value, "difference": user_value - reference_value}
    if lesson.get("analysis") == "tendu":
        user_value = (technique["left_foot_alignment_deviation_degrees"].mean() + technique["right_foot_alignment_deviation_degrees"].mean()) / 2
        reference_value = (reference["left_foot_alignment_deviation_degrees"].mean() + reference["right_foot_alignment_deviation_degrees"].mean()) / 2
        return {"metric": "average foot deviation", "user": float(user_value), "reference": float(reference_value), "difference": float(user_value - reference_value)}
    if lesson.get("analysis") == "arabesque" and "supporting_hip_offset_ratio" in technique.columns and "supporting_hip_offset_ratio" in reference.columns:
        comparison = {"metric": "arabesque alignment"}
        comparable_columns = (
            "supporting_hip_offset_ratio",
            "working_leg_straightness_degrees",
            "torso_lean_degrees",
            "shoulder_hip_offset_ratio",
            "standing_foot_line_degrees",
        )
        for column in comparable_columns:
            if column in technique.columns and column in reference.columns:
                user_value = float(technique[column].mean())
                reference_value = float(reference[column].mean())
                comparison[f"{column}_user"] = user_value
                comparison[f"{column}_reference"] = reference_value
                comparison[f"{column}_difference"] = user_value - reference_value
        return comparison if len(comparison) > 1 else None
    return None


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


@st.cache_data(show_spinner=False, max_entries=4)
def process_uploaded_arabesque(video_bytes: bytes, filename: str, camera_view: str) -> dict[str, str]:
    """Analyze and render one uploaded arabesque clip."""
    if cv2 is None:
        return fallback_uploaded_video(video_bytes, filename, "dance_coach_arabesque_preview_")
    try:
        from src.analyze_arabesque import analyze_video as analyze_arabesque
        from src.render_feedback_video import render
    except ModuleNotFoundError:
        return fallback_uploaded_video(video_bytes, filename, "dance_coach_arabesque_preview_")
    work_dir = Path(tempfile.mkdtemp(prefix="dance_coach_arabesque_"))
    suffix = Path(filename).suffix.lower() or ".mp4"
    input_path = work_dir / f"uploaded_video{suffix}"
    results_dir = work_dir / "results"
    input_path.write_bytes(video_bytes)
    analyze_arabesque(input_path, results_dir)
    feedback_path = render(
        input_path,
        results_dir,
        threshold=0.35,
        analysis="hip_alignment",
        annotations_path=work_dir / "no_annotations.json",
        frame_stride=2,
    )
    return {
        "input": str(input_path),
        "feedback": str(feedback_path),
        "annotated": str(results_dir / "annotated_sample.jpg"),
        "technique": str(results_dir / "technique_results.csv"),
    }


st.markdown('<div class="eyebrow">Technique assessment · lesson review</div>', unsafe_allow_html=True)
st.title("Practice review")
st.markdown('<p class="lede">Upload one short clip, choose the camera angle, and receive a focused, camera-aware practice report.</p>', unsafe_allow_html=True)

selected_lesson = st.selectbox("Choose a lesson", list(LESSONS), index=0)
lesson = LESSONS[selected_lesson]
with st.container(border=True):
    st.markdown(f'<div class="report-kicker">Selected lesson</div><h3 style="margin:.3rem 0 .2rem">{selected_lesson}</h3>', unsafe_allow_html=True)
    st.caption(lesson["level"])
    st.write(lesson["description"])

if lesson.get("analysis") in ("plie", "tendu", "arabesque"):
    camera_view = st.selectbox(
        "Camera angle",
        ["Front", "Side"],
        help="Choose the view that matches your recording. The app uses different practice cues for each angle.",
    )
    if camera_view == "Front":
        st.caption("Front view → knee alignment for plié · foot alignment for tendu · supporting hip for arabesque")
    else:
        st.caption("Side view → posture and depth for plié · foot line for tendu · supporting hip for arabesque")
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
            st.caption("MP4, MOV, or M4V · Maximum length: 60 seconds · One dancer, full body in frame")
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
        loading_label = "Analyzing tendu" if lesson.get("analysis") == "tendu" else f"Analyzing your {selected_lesson.lower()}..."
        with st.spinner(loading_label):
            if lesson.get("analysis") == "tendu":
                processed = process_uploaded_tendu(video_bytes, uploaded_file.name, camera_view)
            elif lesson.get("analysis") == "arabesque":
                processed = process_uploaded_arabesque(video_bytes, uploaded_file.name, camera_view)
            else:
                processed = process_uploaded_video(video_bytes, uploaded_file.name, camera_view)
        video_path = Path(processed["feedback"])
        annotated_path = Path(processed["annotated"])
        technique_path = Path(processed["technique"])
        hosted_preview = processed.get("fallback") == "true"

technique = load_technique_data(technique_path)
if lesson.get("analysis") == "arabesque":
    with st.spinner("Preparing your Arabesque feedback..."):
        try:
            reference_comparison = compare_with_reference(lesson, camera_view, technique)
        except (KeyError, OSError, RuntimeError, ValueError):
            # Never hide the dancer's own analysis if a reference asset is unavailable.
            reference_comparison = None
else:
    reference_comparison = None
pose_quality = None
if technique is not None and not technique.empty:
    total_frames = len(pd.read_csv(technique_path))
    pose_quality = len(technique) / max(total_frames, 1)

if pose_quality is not None:
    score = round(max(0, min(100, pose_quality * 100)))
    score_label = "Strong tracking" if score >= 80 else "Review conditions" if score >= 60 else "Priority: improve capture"
    score_class = "strong" if score >= 80 else "watch" if score >= 60 else "priority"
else:
    score, score_label, score_class = None, "Hosted preview mode", "watch"

st.markdown('<div class="eyebrow" style="margin-top:2rem">Assessment report</div>', unsafe_allow_html=True)
st.subheader("Your dance correction")
primary_focus = "Stay upright and control the depth" if lesson.get("analysis") == "plie" and camera_view == "Side" else lesson["focus"]
st.markdown('<div class="report-kicker">One focus for this repetition</div>', unsafe_allow_html=True)
st.markdown(f'<h2 style="margin:.35rem 0 .8rem">{primary_focus}</h2>', unsafe_allow_html=True)
st.markdown('<div class="assessment-note">Use the coaching cue below to make one specific adjustment, then repeat the same phrase. The report is about your movement—not a grade.</div>', unsafe_allow_html=True)

with st.expander("Video quality", expanded=False):
    if score is None:
        st.caption("Pose tracking quality is unavailable in hosted preview mode.")
    else:
        quality_col, status_col = st.columns(2)
        quality_col.metric("Usable pose frames", f"{len(technique)}/{len(pd.read_csv(technique_path))}")
        status_col.markdown(f'<span class="status-chip {score_class}">{score_label}</span>', unsafe_allow_html=True)
        st.caption("This is a capture-quality check only. It does not score your ballet technique.")

video_col, cue_col = st.columns([1.55, 1], gap="large")
with video_col:
    with st.container(border=True):
        st.subheader("Practice video")
        st.video(str(video_path))
        if lesson.get("analysis") in ("plie", "tendu", "arabesque"):
            cue_name = "knee" if lesson["analysis"] == "plie" and camera_view == "Front" else "posture" if lesson["analysis"] == "plie" else "supporting hip" if lesson["analysis"] == "arabesque" else "foot alignment"
            if hosted_preview:
                st.caption(f"Selected angle: {camera_view} view · Practice cue: {cue_name}.")
                st.caption("Hosted preview mode: landmark overlays are unavailable in this runtime.")
            else:
                st.caption(f"Analyzed angle: {camera_view} view · Green lines show the {cue_name} cue.")

    with st.container(border=True):
        st.subheader("Slow-motion overlay review")
        st.caption("Review the annotated movement at half speed and jump to the moments that matter most.")
        slow_video_path = make_slow_motion_video(str(video_path))
        moments = key_moments(technique)
        moment_name = st.selectbox("Jump to key moment", list(moments), key="key_moment_name")
        max_seek = max(float(moments.get("Return", 0.0)), 0.1)
        scrub_time = st.slider(
            "Scrub timeline",
            min_value=0.0,
            max_value=max_seek,
            value=min(float(moments[moment_name]), max_seek),
            step=0.1,
            format="%.1f s",
            key="scrub_time",
        )
        st.video(slow_video_path, start_time=int(scrub_time))
        st.caption(f"0.5× playback · starting at {scrub_time:.1f} seconds · red/green overlays remain visible.")

with cue_col:
    with st.container(border=True):
        st.subheader("Today's coaching cue")
        feedback_type = "Knee alignment" if lesson["analysis"] == "plie" and camera_view == "Front" else "Posture and depth" if lesson["analysis"] == "plie" else "Supporting-hip stability" if lesson["analysis"] == "arabesque" else "Foot alignment"
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
        elif lesson.get("analysis") == "arabesque":
            focus_text = lesson["focus"]
            hip_difference = reference_comparison.get("supporting_hip_offset_ratio_difference") if reference_comparison else None
            leg_difference = reference_comparison.get("working_leg_straightness_degrees_difference") if reference_comparison else None
            torso_difference = reference_comparison.get("torso_lean_degrees_difference") if reference_comparison else None
            if hip_difference is not None and hip_difference > 0.04:
                detail = "Your supporting-hip offset is above the lesson's positioning benchmark. Lower the working leg slightly and keep the supporting hip organized over the standing foot."
            elif leg_difference is not None and leg_difference < -3:
                detail = "The lifted leg is less extended than the reference line. Choose a lower height, lengthen through the knee, and keep the torso long rather than arching the lower back."
            elif torso_difference is not None and torso_difference > 4:
                detail = "Your torso is leaning more than the reference line. Keep the shoulders and hips organized, then lift the working leg only as high as you can without collapsing the lower back."
            elif hip_difference is not None and hip_difference < -0.04:
                detail = "Your supporting side is tracking within a strong positioning range. Keep the hip organized over the standing foot as you build height."
            else:
                detail = "As the working leg lifts, keep the supporting hip organized over the standing foot and choose height you can control."
        elif lesson.get("analysis") == "hip_alignment":
            focus_text = lesson["focus"]
            detail = "As the back leg lengthens, keep the working hip down and finish the close to fifth position."
        else:
            focus_text = lesson["focus"]
            detail = "As you bend, keep the front of the ribs stacked above the pelvis."
        st.markdown(f"### {focus_text}")
        if pose_quality is not None and pose_quality >= 0.75:
            st.success("The clip was clear enough to track your full-body pose.")
        else:
            st.warning("Some frames were difficult to track. Treat this correction as tentative and improve the lighting or camera distance next time.")
        st.write(f"{detail} Use the on-screen cue as a practice reminder—not as a grade.")
        st.markdown("#### Strengths")
        st.write("You completed a focused repetition with a clear technique target and a consistent camera view.")
        st.markdown("#### Area to improve")
        st.write(f"Prioritize one adjustment: {focus_text.lower()}.")
        st.success("Try one slower repetition, then replay the clip.")

    if annotated_path.exists():
        with st.container(border=True):
            st.subheader("What the coach tracks")
            st.image(str(annotated_path), width="stretch")
            st.caption("Pose landmarks and the alignment line used for this practice cue.")

st.subheader("A quick read of this repetition")
if technique is not None and not technique.empty:
    usable_count = len(technique)
    total_count = len(pd.read_csv(technique_path))
    metric_cols = st.columns(2)
    if lesson.get("analysis") == "plie" and camera_view == "Front":
        left_offset = technique["left_knee_to_toe_offset"].mean()
        right_offset = technique["right_knee_to_toe_offset"].mean()
        torso = technique["torso_lean_degrees"].mean()
        metric_cols[0].metric("Left knee offset", f"{left_offset:.2f}")
        metric_cols[1].metric("Right knee offset", f"{right_offset:.2f}")
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
        metric_cols[0].metric("Average torso lean", f"{torso:.1f}°")
        metric_cols[1].metric("Average knee angle", f"{depth:.1f}°")
        st.line_chart(
            technique.set_index("timestamp_seconds")[["torso_lean_degrees", "plie_depth_angle"]],
            y_label="Side-view proxy",
            x_label="Time (seconds)",
        )
        st.caption("Side-view feedback focuses on staying upright and maintaining a controlled plié depth.")
    elif lesson.get("analysis") == "tendu":
        left_alignment = technique["left_foot_alignment_deviation_degrees"].mean()
        right_alignment = technique["right_foot_alignment_deviation_degrees"].mean()
        metric_cols[0].metric("Left foot deviation", f"{left_alignment:.1f}°")
        metric_cols[1].metric("Right foot deviation", f"{right_alignment:.1f}°")
        st.line_chart(
            technique.set_index("timestamp_seconds")[[
                "left_foot_alignment_deviation_degrees",
                "right_foot_alignment_deviation_degrees",
            ]],
            y_label="Foot alignment deviation",
            x_label="Time (seconds)",
        )
        st.caption("Larger deviation is a camera-dependent cue to check for sickling or winging.")
    elif lesson.get("analysis") == "arabesque" and "supporting_hip_offset_ratio" in technique.columns:
        metric_cols[0].metric("Lifted-leg line", f"{technique['working_leg_straightness_degrees'].mean():.0f}°")
        metric_cols[1].metric("Torso lean", f"{technique['torso_lean_degrees'].mean():.1f}°")
        chart_columns = [
            column for column in (
                "supporting_hip_offset_ratio",
                "working_leg_straightness_degrees",
                "torso_lean_degrees",
                "shoulder_hip_offset_ratio",
                "standing_foot_line_degrees",
            )
            if column in technique.columns
        ]
        st.line_chart(technique.set_index("timestamp_seconds")[chart_columns], y_label="Camera-dependent alignment measures", x_label="Time (seconds)")
        st.caption("The lifted-leg line, torso organization, shoulder–hip relationship, and standing-foot line are camera-dependent proxies—not anatomical grades.")
    elif "supporting_hip_offset_ratio" in technique.columns:
        metric_column = "supporting_hip_offset_ratio"
        metric_cols[0].metric("Average hip offset", f"{technique[metric_column].mean():.2f}")
        metric_cols[1].metric("Peak hip offset", f"{technique[metric_column].max():.2f}")
        st.line_chart(technique.set_index("timestamp_seconds")[metric_column], y_label="Hip-to-foot offset ratio", x_label="Time (seconds)")
    else:
        metric_column = "torso_lean_degrees"
        metric_cols[0].metric("Average torso lean", f"{technique[metric_column].mean():.1f}°")
        metric_cols[1].metric("Peak torso lean", f"{technique[metric_column].max():.1f}°")
        st.line_chart(technique.set_index("timestamp_seconds")[metric_column], y_label="Torso lean (degrees)", x_label="Time (seconds)")
else:
    st.info("Technique measurements are not available for this lesson yet.")

with st.container(border=True):
    st.subheader("Save this practice session")
    st.caption("Keep this review private in your session log so future attempts can be compared like with like.")
    session_note = st.text_area("How did it feel?", placeholder="Example: Easier to keep the left knee tracking, but I lost the line near the bottom of the plié.", key="session_note")
    session_feel = st.radio("Overall feel", ["Harder than expected", "About the same", "Clearer than before"], horizontal=True, key="session_feel")
    if st.button("Save to practice log", type="primary", key="save_review_session"):
        save_review_session(
            {
                "date": pd.Timestamp.now(tz="UTC").isoformat(),
                "exercise": selected_lesson,
                "camera_view": camera_view,
                "metrics": session_metric_snapshot(lesson, camera_view, technique),
                "confidence": float(pose_quality or 0.0),
                "cue": focus_text,
                "note": session_note,
                "feel": session_feel,
            }
        )
        st.success("Saved to your private practice log.")

with st.expander("How to use this feedback"):
    st.markdown("- Pause when the red cue appears.\n- Make one small adjustment, then try the phrase again.\n- Keep the camera angle and distance consistent between attempts.\n\nThis is a camera-dependent practice aid, not a ballet grade, diagnosis, or replacement for an instructor.")
