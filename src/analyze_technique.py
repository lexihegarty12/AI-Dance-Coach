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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "pose_landmarker_lite.task"
LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP = 11, 12, 23, 24


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


def analyze_video(video_path: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "technique_results.csv"
    frame_path = output_dir / "annotated_sample.jpg"

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_index = max(0, frame_count // 2)
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

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = pose.detect_for_video(image, int(frame_index / fps * 1000))
            lean = None
            confidence = None
            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                lean = torso_lean_degrees(landmarks)
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
    average = sum(usable) / len(usable) if usable else 0.0
    print(f"Analyzed {len(rows)} frames from {video_path.name}")
    print(f"Frames with usable posture landmarks: {len(usable)}/{len(rows)}")
    print(f"Average torso lean: {average:.1f} degrees")
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
