"""Analyze a single-dancer video for a simple posture proxy.

This first MVP measures torso lean as the angle between the shoulder-center to
hip-center line and the vertical axis. It is a camera-dependent practice cue,
not a ballet grade or medical assessment.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

try:
    from .movement_metrics import knee_flexion_angle, knee_to_toe_offset
except ImportError:  # Support direct execution: python src/analyze_technique.py ...
    from movement_metrics import knee_flexion_angle, knee_to_toe_offset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "pose_landmarker_lite.task"
LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP = 11, 12, 23, 24
LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE = 25, 26, 27, 28
LEFT_FOOT, RIGHT_FOOT = 31, 32


def torso_lean_degrees(landmarks: object) -> float | None:
    """Return torso lean from vertical in degrees, or None if landmarks are weak."""
    left_shoulder = landmarks[LEFT_SHOULDER]
    right_shoulder = landmarks[RIGHT_SHOULDER]
    left_hip = landmarks[LEFT_HIP]
    right_hip = landmarks[RIGHT_HIP]

    points = (left_shoulder, right_shoulder, left_hip, right_hip)
    if min(point.visibility for point in points) < 0.55:
        return None

    shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
    shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    hip_x = (left_hip.x + right_hip.x) / 2
    hip_y = (left_hip.y + right_hip.y) / 2

    # Image y increases downward. The absolute angle keeps the metric simple.
    dx = shoulder_x - hip_x
    dy = hip_y - shoulder_y
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def plie_metrics(landmarks: object) -> tuple[float | None, float | None, float | None]:
    """Return left/right knee-to-toe offset and mean knee angle.

    These are front-view image proxies. Offset is normalized by hip width so
    it is less sensitive to distance from the camera.
    """
    indices = (
        LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE,
        LEFT_ANKLE, RIGHT_ANKLE, LEFT_FOOT, RIGHT_FOOT,
    )
    points = [landmarks[index] for index in indices]
    if min(point.visibility for point in points) < 0.55:
        return None, None, None

    left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle, left_foot, right_foot = points
    hip_width = abs(left_hip.x - right_hip.x)
    left_offset = knee_to_toe_offset(left_knee, left_foot, hip_width)
    right_offset = knee_to_toe_offset(right_knee, right_foot, hip_width)
    left_angle = knee_flexion_angle(left_hip, left_knee, left_ankle)
    right_angle = knee_flexion_angle(right_hip, right_knee, right_ankle)
    return left_offset, right_offset, (left_angle + right_angle) / 2


def analyze_video(video_path: Path, output_dir: Path, frame_stride: int = 1) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "technique_results.csv"
    frame_path = output_dir / "annotated_sample.jpg"

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    rotation = int(round(capture.get(cv2.CAP_PROP_ORIENTATION_META) or 0)) % 360
    frame_stride = max(1, int(frame_stride))
    sample_index = max(0, (frame_count // 2) // frame_stride * frame_stride)
    rows: list[dict[str, object]] = []
    annotated_sample = None

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Missing pose model at {MODEL_PATH}. See README.md for the download command."
        )

    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(
            model_asset_path=str(MODEL_PATH),
            delegate=mp_python.BaseOptions.Delegate.CPU,
        ),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    with vision.PoseLandmarker.create_from_options(options) as pose:
        frame_index = 0
        while True:
            success, frame = capture.read()
            if not success:
                break

            if frame_index % frame_stride != 0:
                frame_index += 1
                continue

            # OpenCV may expose the phone's rotation metadata without applying
            # it to decoded frames. Pose landmarks are not meaningful until
            # the dancer is upright in image coordinates.
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
            rgb_frame = cv2.cvtColor(inference_frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = pose.detect_for_video(image, int(frame_index / fps * 1000))
            lean = None
            left_knee_offset = None
            right_knee_offset = None
            plie_depth_angle = None
            confidence = None
            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                lean = torso_lean_degrees(landmarks)
                left_knee_offset, right_knee_offset, plie_depth_angle = plie_metrics(landmarks)
                relevant = [
                    landmarks[index]
                    for index in (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP)
                ]
                confidence = min(point.visibility for point in relevant)
                if frame_index == sample_index:
                    annotated_sample = frame.copy()
                    for point in landmarks:
                        x = int(point.x * annotated_sample.shape[1])
                        y = int(point.y * annotated_sample.shape[0])
                        cv2.circle(annotated_sample, (x, y), 4, (0, 220, 0), -1)
                    label = (
                        f"Torso lean: {lean:.1f} deg"
                        if lean is not None
                        else "Torso lean: low confidence"
                    )
                    cv2.putText(
                        annotated_sample,
                        label,
                        (24, 42),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 220, 0),
                        2,
                        cv2.LINE_AA,
                    )

            rows.append(
                {
                    "frame_index": frame_index,
                    "timestamp_seconds": round(frame_index / fps, 3),
                    "torso_lean_degrees": None if lean is None else round(lean, 3),
                    "left_knee_to_toe_offset": None if left_knee_offset is None else round(left_knee_offset, 3),
                    "right_knee_to_toe_offset": None if right_knee_offset is None else round(right_knee_offset, 3),
                    "plie_depth_angle": None if plie_depth_angle is None else round(plie_depth_angle, 3),
                    "confidence": None if confidence is None else round(confidence, 3),
                }
            )
            frame_index += 1

    capture.release()
    if annotated_sample is None:
        raise RuntimeError("No usable pose landmarks were detected in the video.")

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    cv2.imwrite(str(frame_path), annotated_sample)

    usable = [row["torso_lean_degrees"] for row in rows if row["torso_lean_degrees"] is not None]
    left_offsets = [row["left_knee_to_toe_offset"] for row in rows if row["left_knee_to_toe_offset"] is not None]
    right_offsets = [row["right_knee_to_toe_offset"] for row in rows if row["right_knee_to_toe_offset"] is not None]
    depths = [row["plie_depth_angle"] for row in rows if row["plie_depth_angle"] is not None]
    average = sum(usable) / len(usable) if usable else 0.0
    print(f"Analyzed {len(rows)} frames from {video_path.name}")
    print(f"Frames with usable posture landmarks: {len(usable)}/{len(rows)}")
    print(f"Average torso lean: {average:.1f} degrees")
    if left_offsets and right_offsets:
        average_left_offset = sum(left_offsets) / len(left_offsets)
        average_right_offset = sum(right_offsets) / len(right_offsets)
        print(f"Average knee-to-toe offset: left {average_left_offset:.3f}, right {average_right_offset:.3f}")
        if max(average_left_offset, average_right_offset) > 0.35:
            print("Primary correction: Keep your knees tracking over your toes.")
        else:
            print("Primary correction: Knee tracking looks reasonably consistent in this view.")
    if depths:
        print(f"Plie depth angle: mean {sum(depths) / len(depths):.1f} degrees, range {min(depths):.1f}-{max(depths):.1f}")
    print(f"Results: {csv_path}")
    print(f"Annotated sample: {frame_path}")
    return csv_path, frame_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze single-dancer posture.")
    parser.add_argument("video", type=Path, help="Path to a video file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis_output"),
        help="Directory for CSV results and annotated frame",
    )
    args = parser.parse_args()
    analyze_video(args.video, args.output_dir)


if __name__ == "__main__":
    main()
