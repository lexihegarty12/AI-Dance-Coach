"""Create a visual review sheet pairing video frames with posture measurements."""

from __future__ import annotations

import csv
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "test_video1.mov"
RESULTS = ROOT / "analysis_output" / "technique_results.csv"
OUT = ROOT / "analysis_output"


def load_measurements() -> list[dict[str, float]]:
    with RESULTS.open(newline="") as handle:
        return [
            {
                "frame_index": int(row["frame_index"]),
                "timestamp_seconds": float(row["timestamp_seconds"]),
                "torso_lean_degrees": float(row["torso_lean_degrees"]),
            }
            for row in csv.DictReader(handle)
            if row["torso_lean_degrees"]
        ]


def main() -> None:
    measurements = load_measurements()
    if not measurements:
        raise RuntimeError("No usable measurements found.")

    selected = [measurements[int(i * (len(measurements) - 1) / 5)] for i in range(6)]
    capture = cv2.VideoCapture(str(VIDEO))
    frames = []
    for measurement in selected:
        capture.set(cv2.CAP_PROP_POS_FRAMES, measurement["frame_index"])
        ok, frame = capture.read()
        if not ok:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        label = (
            f"{measurement['timestamp_seconds']:.1f}s   "
            f"torso lean: {measurement['torso_lean_degrees']:.1f}°"
        )
        cv2.putText(frame, label, (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 230, 0), 2)
        frames.append(frame)
    capture.release()

    height, width = frames[0].shape[:2]
    sheet = cv2.cvtColor(cv2.hconcat([frames[0], frames[0]]), cv2.COLOR_RGB2BGR)
    sheet = cv2.vconcat([sheet, sheet, sheet])
    for index, frame in enumerate(frames):
        row, col = divmod(index, 2)
        sheet[row * height : (row + 1) * height, col * width : (col + 1) * width] = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(OUT / "technique_review_sheet.jpg"), sheet)

    times = [row["timestamp_seconds"] for row in measurements]
    values = [row["torso_lean_degrees"] for row in measurements]
    chart = 255 * __import__("numpy").ones((520, 1100, 3), dtype="uint8")
    left, top, right, bottom = 100, 55, 1040, 450
    max_time = max(times) or 1.0
    max_value = max(values) or 1.0
    max_value = max(5.0, max_value * 1.1)
    for tick in range(0, 6):
        y = bottom - int((bottom - top) * tick / 5)
        cv2.line(chart, (left, y), (right, y), (220, 220, 220), 1)
        cv2.putText(chart, f"{max_value * tick / 5:.0f}", (35, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (70, 70, 70), 1)
    points = [
        (left + int((right - left) * time / max_time), bottom - int((bottom - top) * value / max_value))
        for time, value in zip(times, values)
    ]
    for first, second in zip(points, points[1:]):
        cv2.line(chart, first, second, (35, 150, 80), 2)
    cv2.line(chart, (left, top), (left, bottom), (50, 50, 50), 2)
    cv2.line(chart, (left, bottom), (right, bottom), (50, 50, 50), 2)
    cv2.putText(chart, "Torso lean over time (usable pose frames)", (left, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (30, 30, 30), 2)
    cv2.putText(chart, "time (seconds)", (left + 380, 495), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 50, 50), 1)
    cv2.putText(chart, "lean (degrees)", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 50, 50), 1)
    cv2.imwrite(str(OUT / "torso_lean_over_time.png"), chart)

    print(f"Review sheet: {OUT / 'technique_review_sheet.jpg'}")
    print(f"Chart: {OUT / 'torso_lean_over_time.png'}")


if __name__ == "__main__":
    main()
