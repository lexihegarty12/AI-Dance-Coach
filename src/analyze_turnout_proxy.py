"""Estimate lower-body alignment and a cautious foot-orientation proxy."""

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
    from .movement_metrics import (
        foot_to_lower_leg_angle,
        knee_to_toe_alignment_angle,
        knee_to_toe_offset,
    )
except ImportError:
    from movement_metrics import (
        foot_to_lower_leg_angle,
        knee_to_toe_alignment_angle,
        knee_to_toe_offset,
    )

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "pose_landmarker_lite.task"
LANDMARKS = {"left_hip": 23, "right_hip": 24, "left_knee": 25, "right_knee": 26, "left_ankle": 27, "right_ankle": 28, "left_heel": 29, "right_heel": 30, "left_foot_index": 31, "right_foot_index": 32}


def foot_angle(heel: object, toe: object) -> float:
    return math.degrees(math.atan2(-(toe.y - heel.y), toe.x - heel.x))


def working_foot(points: list[object]) -> tuple[str | None, float | None]:
    """Choose the more extended foot, or return ambiguous when feet are close."""
    hip_x = (points[23].x + points[24].x) / 2
    hip_y = (points[23].y + points[24].y) / 2
    left_distance = math.hypot(points[31].x - hip_x, points[31].y - hip_y)
    right_distance = math.hypot(points[32].x - hip_x, points[32].y - hip_y)
    largest = max(left_distance, right_distance, 1e-6)
    if abs(left_distance - right_distance) / largest < 0.10:
        return None, None
    if left_distance > right_distance:
        deviation = abs(90 - foot_to_lower_leg_angle(points[25], points[27], points[29], points[31]))
        return "left", deviation
    deviation = abs(90 - foot_to_lower_leg_angle(points[26], points[28], points[30], points[32]))
    return "right", deviation


def analyze(video_path: Path, output_dir: Path, frame_stride: int = 2) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "turnout_proxy_results.csv"
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_stride = max(1, int(frame_stride))
    rotation = int(round(capture.get(cv2.CAP_PROP_ORIENTATION_META) or 0)) % 360
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_index = max(0, (frame_count // 2) // frame_stride * frame_stride)
    annotated_path = output_dir / "annotated_sample.jpg"
    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL_PATH), delegate=mp_python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    rows = []
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
            row = {
                "frame_index": frame_index,
                "timestamp_seconds": round(frame_index / fps, 3),
                "left_foot_orientation_degrees": "",
                "right_foot_orientation_degrees": "",
                "left_knee_ankle_offset": "",
                "right_knee_ankle_offset": "",
                "left_knee_to_toe_alignment_degrees": "",
                "right_knee_to_toe_alignment_degrees": "",
                "left_knee_to_toe_offset": "",
                "right_knee_to_toe_offset": "",
                "left_foot_to_lower_leg_degrees": "",
                "right_foot_to_lower_leg_degrees": "",
                "left_foot_alignment_deviation_degrees": "",
                "right_foot_alignment_deviation_degrees": "",
                "working_foot": "",
                "working_foot_alignment_deviation_degrees": "",
                "confidence": "",
            }
            if result.pose_landmarks:
                points = result.pose_landmarks[0]
                confidence = min(points[index].visibility for index in LANDMARKS.values())
                if confidence >= 0.55:
                    hip_width = max(abs(points[24].x - points[23].x), 1e-6)
                    row.update(
                        {
                            "left_foot_orientation_degrees": round(foot_angle(points[29], points[31]), 3),
                            "right_foot_orientation_degrees": round(foot_angle(points[30], points[32]), 3),
                            "left_knee_ankle_offset": round(abs(points[25].x - points[27].x) / hip_width, 3),
                            "right_knee_ankle_offset": round(abs(points[26].x - points[28].x) / hip_width, 3),
                            "left_knee_to_toe_alignment_degrees": round(knee_to_toe_alignment_angle(points[25], points[31]), 3),
                            "right_knee_to_toe_alignment_degrees": round(knee_to_toe_alignment_angle(points[26], points[32]), 3),
                            "left_knee_to_toe_offset": round(knee_to_toe_offset(points[25], points[31], hip_width), 3),
                            "right_knee_to_toe_offset": round(knee_to_toe_offset(points[26], points[32], hip_width), 3),
                            "left_foot_to_lower_leg_degrees": round(foot_to_lower_leg_angle(points[25], points[27], points[29], points[31]), 3),
                            "right_foot_to_lower_leg_degrees": round(foot_to_lower_leg_angle(points[26], points[28], points[30], points[32]), 3),
                            "left_foot_alignment_deviation_degrees": round(abs(90 - foot_to_lower_leg_angle(points[25], points[27], points[29], points[31])), 3),
                            "right_foot_alignment_deviation_degrees": round(abs(90 - foot_to_lower_leg_angle(points[26], points[28], points[30], points[32])), 3),
                            "confidence": round(confidence, 3),
                        }
                    )
                    side, deviation = working_foot(points)
                    row["working_foot"] = side or "ambiguous"
                    row["working_foot_alignment_deviation_degrees"] = "" if deviation is None else round(deviation, 3)
                    if frame_index == sample_index:
                        annotated = frame.copy()
                        color = (0, 220, 0)
                        left_dev = row["left_foot_alignment_deviation_degrees"]
                        right_dev = row["right_foot_alignment_deviation_degrees"]
                        if max(left_dev, right_dev) > 25:
                            color = (0, 0, 255)
                        coords = [(int(point.x * annotated.shape[1]), int(point.y * annotated.shape[0])) for point in points]
                        for start, end in ((27, 31), (28, 32)):
                            cv2.line(annotated, coords[start], coords[end], color, 8, cv2.LINE_AA)
                        cv2.putText(annotated, "Foot alignment proxy", (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)
                        cv2.imwrite(str(annotated_path), annotated)
            rows.append(row)
            frame_index += 1
    capture.release()
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Turnout proxy results: {output_csv}")
    print("Caution: interpret only as a 2D camera-dependent proxy, not anatomical turnout.")
    return output_csv, annotated_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.video, args.output_dir)


if __name__ == "__main__":
    main()
