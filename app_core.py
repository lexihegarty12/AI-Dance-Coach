"""Shared data and helpers for the AI Dance Coach demo pages."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "analysis_output"
DEMO_RESULTS_DIR = ROOT / "demo_assets"
ANNOTATIONS_PATH = ROOT / "data" / "coaching_annotations.json"

LESSONS = {
    "Arabesque penché": {"slug": "developpe_arabesque_penche", "description": "A longer dynamic developpé into arabesque penché with a focus on length and support.", "focus": "Keep the hip down and finish the fifth-position close", "level": "Dynamic", "duration": "00:22", "analysis": "hip_alignment"},
}


def result_paths(slug: str) -> dict[str, Path]:
    demo_dir = DEMO_RESULTS_DIR / f"{slug}_results"
    result_dir = demo_dir if demo_dir.exists() else RESULTS_DIR / f"{slug}_results"
    return {"feedback": result_dir / "feedback_video.mp4", "annotated": result_dir / "annotated_sample.jpg", "technique": result_dir / "technique_results.csv"}


def load_technique_data(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    data = pd.read_csv(path)
    metric_column = "supporting_hip_offset_ratio" if "supporting_hip_offset_ratio" in data.columns else "torso_lean_degrees"
    return data.dropna(subset=[metric_column]) if metric_column in data.columns else None


def load_coaching_annotations(slug: str) -> list[dict[str, object]]:
    if not ANNOTATIONS_PATH.exists():
        return []
    payload = json.loads(ANNOTATIONS_PATH.read_text())
    return payload.get(slug, {}).get("annotations", [])
