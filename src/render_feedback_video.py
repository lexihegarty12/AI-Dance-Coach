"""Render dancer-facing visual feedback over a pose-analysis clip."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

try:
    from .movement_metrics import foot_to_lower_leg_angle
except ImportError:
    from movement_metrics import foot_to_lower_leg_angle

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "pose_landmarker_lite.task"
ANNOTATIONS_PATH = ROOT / "data" / "coaching_annotations.json"
CONNECTIONS = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28)]


def torso_lean(points: list[object]) -> tuple[float, tuple[int, int], tuple[int, int]]:
    shoulder = ((points[11].x + points[12].x) / 2, (points[11].y + points[12].y) / 2)
    hip = ((points[23].x + points[24].x) / 2, (points[23].y + points[24].y) / 2)
    degrees = math.degrees(math.atan2(abs(shoulder[0] - hip[0]), abs(hip[1] - shoulder[1])))
    return degrees, (int(shoulder[0] * 1), int(shoulder[1] * 1)), (int(hip[0] * 1), int(hip[1] * 1))


def supporting_hip_alignment(points: list[object]) -> tuple[float, int, int]:
    """Return hip-to-standing-ankle offset as a fraction of standing-leg length."""
    ankle_index = 27 if points[27].y > points[28].y else 28
    hip_index = 23 if ankle_index == 27 else 24
    leg_length = max(abs(points[hip_index].y - points[ankle_index].y), 1e-6)
    offset = abs(points[hip_index].x - points[ankle_index].x) / leg_length
    return offset, hip_index, ankle_index


def plie_knee_offsets(points: list[object]) -> tuple[float, float]:
    hip_width = max(abs(points[23].x - points[24].x), 1e-6)
    left = abs(points[25].x - points[31].x) / hip_width
    right = abs(points[26].x - points[32].x) / hip_width
    return left, right


def tendu_foot_deviations(points: list[object]) -> tuple[float, float]:
    left = abs(90 - foot_to_lower_leg_angle(points[25], points[27], points[29], points[31]))
    right = abs(90 - foot_to_lower_leg_angle(points[26], points[28], points[30], points[32]))
    return left, right


def tendu_working_foot(points: list[object]) -> tuple[str | None, float | None]:
    hip_x = (points[23].x + points[24].x) / 2
    hip_y = (points[23].y + points[24].y) / 2
    left_distance = math.hypot(points[31].x - hip_x, points[31].y - hip_y)
    right_distance = math.hypot(points[32].x - hip_x, points[32].y - hip_y)
    largest = max(left_distance, right_distance, 1e-6)
    if abs(left_distance - right_distance) / largest < 0.10:
        return None, None
    if left_distance > right_distance:
        return "left", abs(90 - foot_to_lower_leg_angle(points[25], points[27], points[29], points[31]))
    return "right", abs(90 - foot_to_lower_leg_angle(points[26], points[28], points[30], points[32]))


def render(video_path: Path, output_dir: Path, threshold: float, analysis: str, annotations_path: Path, frame_stride: int = 1) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "feedback_raw.mp4"
    output_path = output_dir / "feedback_video.mp4"
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_stride = max(1, int(frame_stride))
    rotation = int(round(capture.get(cv2.CAP_PROP_ORIENTATION_META) or 0)) % 360
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if rotation in (90, 270):
        width, height = height, width
    writer = cv2.VideoWriter(str(raw_path), cv2.VideoWriter_fourcc(*"mp4v"), fps / frame_stride, (width, height))
    annotations = []
    tendu_flag_history: list[bool] = []
    if annotations_path.exists():
        annotation_data = json.loads(annotations_path.read_text())
        clip_annotations = annotation_data.get(video_path.stem, {})
        annotations = clip_annotations.get("annotations", [])
    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL_PATH), delegate=mp_python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    with vision.PoseLandmarker.create_from_options(options) as pose:
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_stride != 0:
                frame_index += 1
                continue
            if rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            inference_frame = frame
            longest_edge = max(frame.shape[:2])
            if longest_edge > 960:
                scale = 960 / longest_edge
                inference_frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(inference_frame, cv2.COLOR_BGR2RGB))
            result = pose.detect_for_video(image, int(frame_index / fps * 1000))
            color = (0, 220, 0)
            label = "Ready to review"
            if result.pose_landmarks:
                points = result.pose_landmarks[0]
                if analysis == "plie":
                    relevant_points = (23, 24, 25, 26, 27, 28, 31, 32)
                elif analysis == "tendu":
                    relevant_points = (25, 26, 27, 28, 29, 30, 31, 32)
                else:
                    relevant_points = (11, 12, 23, 24) if analysis == "torso" else (23, 24, 27, 28)
                confidence = min(points[i].visibility for i in relevant_points)
                if confidence < 0.55:
                    color = (0, 200, 255)
                    label = "Pose confidence low - check the view"
                else:
                    if analysis == "plie":
                        left_offset, right_offset = plie_knee_offsets(points)
                        if max(left_offset, right_offset) > threshold:
                            color = (0, 0, 255)
                            label = "Correction: keep your knees tracking over your toes"
                        else:
                            label = "Knee tracking looks consistent in this view"
                    elif analysis == "tendu":
                        working_side, working_deviation = tendu_working_foot(points)
                        if working_deviation is None:
                            color = (0, 200, 255)
                            label = "Foot alignment not assessed - keep the working foot clear"
                            tendu_flag_history.append(False)
                        else:
                            current_flag = working_deviation > threshold
                            tendu_flag_history.append(current_flag)
                            recent = tendu_flag_history[-6:]
                            sustained_flag = len(recent) >= 4 and sum(recent) >= 4
                            if sustained_flag:
                                color = (0, 0, 255)
                                label = "Correction: check the working foot line as you extend"
                            else:
                                label = f"Working foot: {working_side} - alignment within review range"
                    elif analysis == "hip_alignment":
                        offset, hip_index, ankle_index = supporting_hip_alignment(points)
                        timestamp = frame_index / fps
                        time_annotation = next((item for item in annotations if item["start_seconds"] <= timestamp < item["end_seconds"]), None)
                        if time_annotation:
                            color = (0, 0, 255)
                            label = time_annotation["label"]
                        elif offset > threshold:
                            color = (0, 0, 255)
                            label = "Check supporting hip - keep lift through standing side"
                        else:
                            label = "Supporting hip stacked over foot - good"
                    else:
                        lean, _, _ = torso_lean(points)
                        if lean > threshold:
                            color = (0, 0, 255)
                            label = f"Check ribs over hips - torso lean {lean:.1f} deg"
                        else:
                            label = f"Torso lean {lean:.1f} deg - within alert range"
                coords = [(int(point.x * width), int(point.y * height)) for point in points]
                for a, b in CONNECTIONS:
                    cv2.line(frame, coords[a], coords[b], color, 5, cv2.LINE_AA)
                for point in coords:
                    cv2.circle(frame, point, 5, color, -1)
                if analysis == "plie":
                    cv2.line(frame, coords[25], coords[31], color, 8, cv2.LINE_AA)
                    cv2.line(frame, coords[26], coords[32], color, 8, cv2.LINE_AA)
                elif analysis == "tendu":
                    cv2.line(frame, coords[27], coords[31], color, 8, cv2.LINE_AA)
                    cv2.line(frame, coords[28], coords[32], color, 8, cv2.LINE_AA)
                elif analysis == "hip_alignment":
                    cv2.line(frame, coords[hip_index], coords[ankle_index], color, 8, cv2.LINE_AA)
                else:
                    shoulder = ((coords[11][0] + coords[12][0]) // 2, (coords[11][1] + coords[12][1]) // 2)
                    hip = ((coords[23][0] + coords[24][0]) // 2, (coords[23][1] + coords[24][1]) // 2)
                    cv2.line(frame, shoulder, hip, color, 8, cv2.LINE_AA)
            cv2.rectangle(frame, (0, 0), (width, 76), (20, 20, 20), -1)
            cv2.putText(frame, label, (24, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)
            writer.write(frame)
            frame_index += 1
    capture.release()
    writer.release()
    ffmpeg = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", "-i", str(raw_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(output_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raw_path.unlink(missing_ok=True)
    print(f"Feedback video: {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=8.0, help="Visual alert threshold in degrees")
    parser.add_argument("--analysis", choices=("torso", "hip_alignment", "plie", "tendu"), default="torso")
    parser.add_argument("--annotations", type=Path, default=ANNOTATIONS_PATH)
    args = parser.parse_args()
    render(args.video, args.output_dir, args.threshold, args.analysis, args.annotations)


if __name__ == "__main__":
    main()
