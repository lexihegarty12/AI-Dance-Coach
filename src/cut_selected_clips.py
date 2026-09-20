"""Cut user-selected, time-labeled clips from the audition video."""

from __future__ import annotations

import csv
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "Full_Training_Vid.mov"
OUT = ROOT / "analysis_output" / "selected_clips"

CLIPS = [
    ("plies_first", 0, 27, "plies in first"),
    ("plies_fifth", 85, 94, "plies in fifth"),
    ("passe_balance", 255, 260, "passe balance"),
    ("developpe_front", 270, 280, "developpe front"),
    ("developpe_arabesque_penche", 283, 299, "developpe to arabesque penche"),
    ("developpe_side_rond_de_jambe_arabesque", 295, 314, "developpe to the side, rond de jambe to arabesque"),
    ("waltz_pirouettes", 349, 376, "waltz with pirouettes"),
]


def cut_clip(capture: cv2.VideoCapture, fps: float, start: float, end: float, destination: Path) -> int:
    capture.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(
        str(destination), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    frames = 0
    while True:
        timestamp = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if timestamp >= end:
            break
        ok, frame = capture.read()
        if not ok:
            break
        writer.write(frame)
        frames += 1
    writer.release()
    return frames


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(VIDEO))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open {VIDEO}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    manifest = []
    for name, start, end, label in CLIPS:
        destination = OUT / f"{name}.mp4"
        frames = cut_clip(capture, fps, start, end, destination)
        manifest.append({
            "clip_name": name,
            "label": label,
            "start_seconds": start,
            "end_seconds": end,
            "frames_written": frames,
            "file": str(destination),
        })
    capture.release()
    with (OUT / "clip_manifest.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest[0].keys())
        writer.writeheader()
        writer.writerows(manifest)
    for row in manifest:
        print(f"{row['clip_name']}: {row['frames_written']} frames -> {row['file']}")


if __name__ == "__main__":
    main()
