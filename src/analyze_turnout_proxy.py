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

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "pose_landmarker_lite.task"
LANDMARKS = {"left_hip": 23, "right_hip": 24, "left_knee": 25, "right_knee": 26, "left_ankle": 27, "right_ankle": 28, "left_heel": 29, "right_heel": 30, "left_foot_index": 31, "right_foot_index": 32}


def foot_angle(heel: object, toe: object) -> float:
    return math.degrees(math.atan2(-(toe.y - heel.y), toe.x - heel.x))


def analyze(video_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "turnout_proxy_results.csv"
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
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
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = pose.detect_for_video(image, int(frame_index / fps * 1000))
            row = {"frame_index": frame_index, "timestamp_seconds": round(frame_index / fps, 3), "left_foot_orientation_degrees": "", "right_foot_orientation_degrees": "", "left_knee_ankle_offset": "", "right_knee_ankle_offset": "", "confidence": ""}
            if result.pose_landmarks:
                points = result.pose_landmarks[0]
                confidence = min(points[index].visibility for index in LANDMARKS.values())
                if confidence >= 0.55:
                    hip_width = max(abs(points[24].x - points[23].x), 1e-6)
                    row.update({"left_foot_orientation_degrees": round(foot_angle(points[29], points[31]), 3), "right_foot_orientation_degrees": round(foot_angle(points[30], points[32]), 3), "left_knee_ankle_offset": round(abs(points[25].x - points[27].x) / hip_width, 3), "right_knee_ankle_offset": round(abs(points[26].x - points[28].x) / hip_width, 3), "confidence": round(confidence, 3)})
            rows.append(row)
            frame_index += 1
    capture.release()
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Turnout proxy results: {output_csv}")
    print("Caution: interpret only as a 2D camera-dependent proxy, not anatomical turnout.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.video, args.output_dir)


if __name__ == "__main__":
    main()
