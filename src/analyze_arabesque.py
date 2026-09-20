"""Analyze supporting-hip alignment for an arabesque practice clip."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "pose_landmarker_lite.task"


def hip_alignment(landmarks: object) -> tuple[float | None, int, int, float | None]:
    ankle_index = 27 if landmarks[27].y > landmarks[28].y else 28
    hip_index = 23 if ankle_index == 27 else 24
    relevant = (23, 24, 27, 28)
    confidence = min(landmarks[index].visibility for index in relevant)
    if confidence < 0.55:
        return None, hip_index, ankle_index, confidence
    leg_length = max(abs(landmarks[hip_index].y - landmarks[ankle_index].y), 1e-6)
    offset = abs(landmarks[hip_index].x - landmarks[ankle_index].x) / leg_length
    return offset, hip_index, ankle_index, confidence


def analyze_video(video_path: Path, output_dir: Path) -> None:
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
            success, frame = capture.read()
            if not success:
                break
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = pose.detect_for_video(image, int(frame_index / fps * 1000))
            offset = None
            confidence = None
            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                offset, hip_index, ankle_index, confidence = hip_alignment(landmarks)
                if frame_index == sample_index:
                    annotated_sample = frame.copy()
                    height, width = annotated_sample.shape[:2]
                    for point in landmarks:
                        cv2.circle(annotated_sample, (int(point.x * width), int(point.y * height)), 4, (0, 220, 0), -1)
                    hip = (int(landmarks[hip_index].x * width), int(landmarks[hip_index].y * height))
                    ankle = (int(landmarks[ankle_index].x * width), int(landmarks[ankle_index].y * height))
                    cv2.line(annotated_sample, hip, ankle, (0, 220, 0), 8, cv2.LINE_AA)
                    label = f"Supporting hip offset: {offset:.2f}" if offset is not None else "Hip alignment: low confidence"
                    cv2.putText(annotated_sample, label, (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 0), 2, cv2.LINE_AA)
            rows.append({"frame_index": frame_index, "timestamp_seconds": round(frame_index / fps, 3), "supporting_hip_offset_ratio": None if offset is None else round(offset, 4), "confidence": confidence})
            frame_index += 1
    capture.release()
    if annotated_sample is None:
        raise RuntimeError("No usable pose landmarks were detected in the video.")
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    cv2.imwrite(str(frame_path), annotated_sample)
    usable = [row["supporting_hip_offset_ratio"] for row in rows if row["supporting_hip_offset_ratio"] is not None]
    print(f"Analyzed {len(rows)} frames from {video_path.name}")
    print(f"Frames with usable hip landmarks: {len(usable)}/{len(rows)}")
    print(f"Average supporting-hip offset ratio: {sum(usable) / len(usable):.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze supporting-hip alignment in an arabesque clip.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    analyze_video(args.video, args.output_dir)


if __name__ == "__main__":
    main()
