"""Evaluate the current practice cues against the local technique dataset.

This is a small validation report, not a model-training pipeline. It keeps
whole recordings together and reports camera-dependent proxy results alongside
the teacher-provided labels and notes.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd

from analyze_technique import analyze_video
from analyze_turnout_proxy import analyze as analyze_tendu

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "technique_data" / "technique_data_cleaned.csv"
RAW_VIDEO_DIR = ROOT / "raw_dance_vids"


def find_video(filename: str) -> Path | None:
    matches = list(RAW_VIDEO_DIR.rglob(filename))
    if matches:
        return matches[0]
    target = filename.lower()
    for candidate in RAW_VIDEO_DIR.rglob("*"):
        if candidate.is_file() and candidate.name.lower() == target:
            return candidate
    return None


def notes_mention_alignment(notes: str) -> bool:
    return bool(re.search(r"knee|foot|sickl|wing|align|toe|heel|turnout", notes.lower()))


def evaluate(dataset_path: Path, output_dir: Path, frame_stride: int, movement: str | None = None) -> Path:
    dataset = pd.read_csv(dataset_path)
    dataset = dataset[
        dataset["movement_group"].isin(["plie", "tendu"])
        & dataset["camera_view"].isin(["front", "side"])
    ].copy()
    if movement:
        dataset = dataset[dataset["movement_group"] == movement].copy()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for record in dataset.to_dict("records"):
        video_path = find_video(str(record["file_name"]))
        result: dict[str, object] = {
            "video_id": record["video_id"],
            "file_name": record["file_name"],
            "movement_group": record["movement_group"],
            "camera_view": record["camera_view"],
            "overall_label": record["overall_label"],
            "review_status": record["review_status"],
            "correction_notes": record.get("correction_notes", "") or "",
            "video_found": video_path is not None,
            "usable_frame_ratio": "",
            "primary_metric": "",
            "metric_value": "",
            "flag_rate": "",
            "system_cue": "",
            "potential_false_positive": False,
            "error": "",
        }
        if video_path is None:
            result["error"] = "Raw video not found"
            rows.append(result)
            continue

        try:
            result_dir = output_dir / f"video_{record['video_id']}"
            if record["movement_group"] == "plie":
                csv_path, _ = analyze_video(video_path, result_dir, frame_stride=frame_stride)
                measurements = pd.read_csv(csv_path)
                usable = measurements.dropna(subset=["torso_lean_degrees"])
                result["usable_frame_ratio"] = round(len(usable) / max(len(measurements), 1), 3)
                if record["camera_view"] == "front":
                    metric = (usable["left_knee_to_toe_offset"].mean() + usable["right_knee_to_toe_offset"].mean()) / 2
                    result["primary_metric"] = "mean_knee_to_toe_offset"
                    result["metric_value"] = round(metric, 3)
                    flagged = metric > 0.35
                    result["flag_rate"] = round(float((usable["left_knee_to_toe_offset"].combine(usable["right_knee_to_toe_offset"], max) > 0.35).mean()), 3)
                    result["system_cue"] = "knee_tracking" if flagged else "no_primary_correction"
                else:
                    metric = usable["torso_lean_degrees"].mean()
                    result["primary_metric"] = "mean_torso_lean_degrees"
                    result["metric_value"] = round(metric, 3)
                    flagged = metric > 10
                    result["flag_rate"] = round(float((usable["torso_lean_degrees"] > 10).mean()), 3)
                    result["system_cue"] = "torso_control" if flagged else "no_primary_correction"
            else:
                csv_path, _ = analyze_tendu(video_path, result_dir, frame_stride=frame_stride)
                measurements = pd.read_csv(csv_path)
                usable = measurements.dropna(subset=["left_foot_alignment_deviation_degrees"])
                result["usable_frame_ratio"] = round(len(usable) / max(len(measurements), 1), 3)
                working = usable.dropna(subset=["working_foot_alignment_deviation_degrees"])
                metric = working["working_foot_alignment_deviation_degrees"].mean() if not working.empty else float("nan")
                result["primary_metric"] = "mean_working_foot_alignment_deviation_degrees"
                result["metric_value"] = round(metric, 3)
                minimum_quality = float(result["usable_frame_ratio"]) >= 0.75
                threshold = 55 if record["camera_view"] == "side" else 45
                flag_rate = float((working["working_foot_alignment_deviation_degrees"] > threshold).mean()) if not working.empty else 0.0
                result["flag_rate"] = round(flag_rate, 3)
                flagged = minimum_quality and not working.empty and flag_rate >= 0.25
                result["system_cue"] = "foot_alignment_check" if flagged else "no_primary_correction"

            # A good clip with no alignment-related teacher note is the useful
            # false-positive check for this early evaluation.
            result["potential_false_positive"] = bool(
                flagged
                and record["overall_label"] == "good"
                and not notes_mention_alignment(str(result["correction_notes"]))
            )
        except Exception as exc:  # Keep the report moving when one clip fails.
            result["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(result)

    report_path = output_dir / "evaluation_report.csv"
    with report_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis_output" / "technique_data_evaluation")
    parser.add_argument("--frame-stride", type=int, default=8, help="Analyze every Nth frame for a quick validation pass.")
    parser.add_argument("--movement", choices=("plie", "tendu"), help="Evaluate only one movement group.")
    args = parser.parse_args()
    report = evaluate(args.dataset, args.output_dir, max(1, args.frame_stride), args.movement)
    data = pd.read_csv(report)
    print(f"Evaluated {len(data)} clips")
    print(f"Videos found: {int(data['video_found'].sum())}/{len(data)}")
    print(f"Potential false positives: {int(data['potential_false_positive'].sum())}")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
