"""Analyze supporting-hip alignment for an arabesque practice clip."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from types import SimpleNamespace

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "pose_landmarker_lite.task"


def point_distance(first: object, second: object) -> float:
    return math.hypot(first.x - second.x, first.y - second.y)


def joint_angle(first: object, vertex: object, last: object) -> float:
    """Return the angle at vertex in degrees."""
    first_vector = (first.x - vertex.x, first.y - vertex.y)
    last_vector = (last.x - vertex.x, last.y - vertex.y)
    denominator = math.hypot(*first_vector) * math.hypot(*last_vector)
    if denominator <= 1e-8:
        return 0.0
    cosine = max(-1.0, min(1.0, sum(a * b for a, b in zip(first_vector, last_vector)) / denominator))
    return math.degrees(math.acos(cosine))


def arabesque_metrics(landmarks: object) -> dict[str, float | int | None]:
    """Extract cautious, camera-dependent Arabesque positioning measures."""
    ankle_index = 27 if landmarks[27].y > landmarks[28].y else 28
    support_side = 0 if ankle_index == 27 else 1
    support_hip_index = 23 if support_side == 0 else 24
    support_knee_index = 25 if support_side == 0 else 26
    working_hip_index = 24 if support_side == 0 else 23
    working_knee_index = 26 if support_side == 0 else 25
    working_ankle_index = 28 if support_side == 0 else 27
    support_foot_index = 31 if support_side == 0 else 32
    relevant = (11, 12, 23, 24, support_knee_index, ankle_index, working_hip_index, working_knee_index, working_ankle_index)
    confidence = min(landmarks[index].visibility for index in relevant)
    if confidence < 0.55:
        return {
            "supporting_hip_offset_ratio": None,
            "working_leg_straightness_degrees": None,
            "torso_lean_degrees": None,
            "shoulder_hip_offset_ratio": None,
            "standing_foot_line_degrees": None,
            "supporting_side": support_side,
            "confidence": confidence,
        }

    left_shoulder, right_shoulder = landmarks[11], landmarks[12]
    left_hip, right_hip = landmarks[23], landmarks[24]
    shoulder_mid = SimpleNamespace(
        x=(left_shoulder.x + right_shoulder.x) / 2,
        y=(left_shoulder.y + right_shoulder.y) / 2,
    )
    hip_mid = SimpleNamespace(
        x=(left_hip.x + right_hip.x) / 2,
        y=(left_hip.y + right_hip.y) / 2,
    )
    torso_length = max(point_distance(shoulder_mid, hip_mid), 1e-6)
    torso_lean = abs(math.degrees(math.atan2(shoulder_mid.x - hip_mid.x, hip_mid.y - shoulder_mid.y)))
    shoulder_hip_offset = abs(shoulder_mid.x - hip_mid.x) / torso_length
    shoulder_line = math.degrees(math.atan2(right_shoulder.y - left_shoulder.y, right_shoulder.x - left_shoulder.x))
    hip_line = math.degrees(math.atan2(right_hip.y - left_hip.y, right_hip.x - left_hip.x))
    shoulder_hip_line_difference = abs(shoulder_line - hip_line)
    shoulder_hip_line_difference = min(shoulder_hip_line_difference, 180 - shoulder_hip_line_difference)

    support_hip = landmarks[support_hip_index]
    support_ankle = landmarks[ankle_index]
    support_leg_length = max(point_distance(support_hip, support_ankle), 1e-6)
    working_leg_straightness = joint_angle(landmarks[working_hip_index], landmarks[working_knee_index], landmarks[working_ankle_index])
    support_foot = landmarks[support_foot_index]
    standing_foot_line = abs(math.degrees(math.atan2(support_foot.y - support_ankle.y, support_foot.x - support_ankle.x)))

    return {
        "supporting_hip_offset_ratio": abs(support_hip.x - support_ankle.x) / support_leg_length,
        "working_leg_straightness_degrees": working_leg_straightness,
        "torso_lean_degrees": torso_lean,
        "shoulder_hip_offset_ratio": shoulder_hip_offset,
        "shoulder_hip_line_difference_degrees": shoulder_hip_line_difference,
        "standing_foot_line_degrees": standing_foot_line,
        "supporting_side": support_side,
        "confidence": confidence,
    }


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
                metrics = arabesque_metrics(landmarks)
                offset = metrics["supporting_hip_offset_ratio"]
                confidence = metrics["confidence"]
                ankle_index = 27 if metrics["supporting_side"] == 0 else 28
                hip_index = 23 if metrics["supporting_side"] == 0 else 24
                if frame_index == sample_index:
                    annotated_sample = frame.copy()
                    height, width = annotated_sample.shape[:2]
                    for point in landmarks:
                        cv2.circle(annotated_sample, (int(point.x * width), int(point.y * height)), 4, (0, 220, 0), -1)
                    hip = (int(landmarks[hip_index].x * width), int(landmarks[hip_index].y * height))
                    ankle = (int(landmarks[ankle_index].x * width), int(landmarks[ankle_index].y * height))
                    cv2.line(annotated_sample, hip, ankle, (0, 220, 0), 8, cv2.LINE_AA)
                    label = f"Hip offset {offset:.2f} · Leg {metrics['working_leg_straightness_degrees']:.0f}°" if offset is not None else "Arabesque alignment: low confidence"
                    cv2.putText(annotated_sample, label, (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 0), 2, cv2.LINE_AA)
            else:
                metrics = {"supporting_hip_offset_ratio": None, "working_leg_straightness_degrees": None, "torso_lean_degrees": None, "shoulder_hip_offset_ratio": None, "shoulder_hip_line_difference_degrees": None, "standing_foot_line_degrees": None, "confidence": None}
            rows.append({
                "frame_index": frame_index,
                "timestamp_seconds": round(frame_index / fps, 3),
                "supporting_hip_offset_ratio": metrics["supporting_hip_offset_ratio"],
                "working_leg_straightness_degrees": metrics["working_leg_straightness_degrees"],
                "torso_lean_degrees": metrics["torso_lean_degrees"],
                "shoulder_hip_offset_ratio": metrics["shoulder_hip_offset_ratio"],
                "shoulder_hip_line_difference_degrees": metrics.get("shoulder_hip_line_difference_degrees"),
                "standing_foot_line_degrees": metrics["standing_foot_line_degrees"],
                "confidence": metrics["confidence"],
            })
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
