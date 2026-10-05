"""Shared data and helpers for the AI Dance Coach practice app."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "analysis_output"
DEMO_RESULTS_DIR = ROOT / "demo_assets"
ANNOTATIONS_PATH = ROOT / "data" / "coaching_annotations.json"

LESSONS = {
    "Demi-plié in first": {
        "slug": "bad_plie_front_metrics",
        "description": "A front-view demi-plié in first position with a focus on knee tracking.",
        "focus": "Keep your knees tracking over your toes",
        "level": "Foundational",
        "duration": "00:36",
        "analysis": "plie",
    },
    "Tendu": {
        "slug": "tendu_front_alignment",
        "description": "A front-view tendu with a focus on reaching through the foot without sickling.",
        "focus": "Keep the foot aligned as you extend",
        "level": "Foundational",
        "duration": "00:35",
        "analysis": "tendu",
    },
}


def result_paths(slug: str) -> dict[str, Path]:
    demo_dir = DEMO_RESULTS_DIR / f"{slug}_results"
    result_dir = demo_dir if demo_dir.exists() else RESULTS_DIR / f"{slug}_results"
    technique_name = "turnout_proxy_results.csv" if slug == "tendu_front_alignment" else "technique_results.csv"
    return {"feedback": result_dir / "feedback_video.mp4", "annotated": result_dir / "annotated_sample.jpg", "technique": result_dir / technique_name}


def load_technique_data(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    data = pd.read_csv(path)
    metric_column = next(
        (
            column
            for column in (
                "supporting_hip_offset_ratio",
                "torso_lean_degrees",
                "left_foot_alignment_deviation_degrees",
            )
            if column in data.columns
        ),
        None,
    )
    return data.dropna(subset=[metric_column]) if metric_column in data.columns else None


def load_coaching_annotations(slug: str) -> list[dict[str, object]]:
    if not ANNOTATIONS_PATH.exists():
        return []
    payload = json.loads(ANNOTATIONS_PATH.read_text())
    return payload.get(slug, {}).get("annotations", [])
