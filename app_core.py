"""Shared data and helpers for the Ballet Technique Analysis Platform."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "analysis_output"
DEMO_RESULTS_DIR = ROOT / "demo_assets"
ANNOTATIONS_PATH = ROOT / "data" / "coaching_annotations.json"
REFERENCE_LIBRARY_PATH = ROOT / "data" / "reference_library.json"

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

CORRECTION_PATHWAYS = {
    "Torso stability in arabesque": {
        "summary": "Build control so the torso supports the arabesque without collapsing or shifting sideways.",
        "issue": "torso_stability",
        "positions": "Arabesque and arabesque penché",
        "cue": "Keep the ribs organized over the supporting hip while the working leg lengthens away.",
        "exercises": [
            ("Wall-supported arabesque", "3 holds per side", "Use the wall lightly and notice whether the ribs stay quiet as the leg lifts."),
            ("Low arabesque tendu", "6 slow repetitions per side", "Slide the working leg back and return without letting the standing hip hike."),
            ("Arabesque hold", "3 holds of 10–15 seconds", "Choose a lower height that lets you keep the torso and supporting leg steady."),
        ],
        "resources": [
            ("Teacher video search: arabesque alignment", "YouTube search", "https://www.youtube.com/results?search_query=ballet+teacher+arabesque+alignment+supporting+hip"),
            ("Teacher video search: arabesque penché technique", "YouTube search", "https://www.youtube.com/results?search_query=ballet+teacher+arabesque+penche+technique"),
        ],
    },
    "Supporting-leg alignment in plié": {
        "summary": "Improve the relationship between the hip, knee, and toes while bending and rising.",
        "issue": "supporting_leg_alignment",
        "positions": "First position and demi-plié",
        "cue": "Let the knees follow the direction of the toes without forcing turnout from the feet.",
        "exercises": [
            ("Slow demi-plié", "8 repetitions", "Lower for four counts and rise for four, keeping the weight balanced across the feet."),
            ("Parallel-to-first alignment check", "2 minutes", "Practice a small bend in parallel, then repeat in first position with the same knee tracking."),
            ("Supported single-leg bend", "5 repetitions per side", "Use a barre or chair and keep the knee directed over the middle toes."),
        ],
        "resources": [
            ("Teacher video search: ballet knee tracking in plié", "YouTube search", "https://www.youtube.com/results?search_query=ballet+teacher+knee+tracking+plie"),
            ("Teacher video search: ballet turnout and knee alignment", "YouTube search", "https://www.youtube.com/results?search_query=ballet+teacher+turnout+knee+alignment"),
        ],
    },
    "Foot alignment in tendu": {
        "summary": "Build a clearer, longer foot pathway while reducing sickling or rolling during tendu.",
        "issue": "foot_alignment",
        "positions": "Tendu from first position",
        "cue": "Reach through the heel, ball of the foot, and toes while keeping the ankle aligned with the leg.",
        "exercises": [
            ("Tendu pathway", "8 repetitions per side", "Brush through the floor slowly and articulate the foot on the way out and in."),
            ("Toe-point articulation", "2 sets per side", "Practice the final point without gripping the toes or rolling the ankle."),
            ("Slow tendu with pause", "6 repetitions per side", "Pause at full extension and check that the foot line matches the knee and hip."),
        ],
        "resources": [
            ("Teacher video search: ballet tendu foot articulation", "YouTube search", "https://www.youtube.com/results?search_query=ballet+teacher+tendu+foot+articulation"),
            ("Teacher video search: ballet sickling correction", "YouTube search", "https://www.youtube.com/results?search_query=ballet+teacher+sickling+foot+correction"),
        ],
    },
}

# Curated teaching clips shown in the training plan. The notes are concise,
# paraphrased coaching takeaways rather than copied transcript text.
VIDEO_LIBRARY = {
    "Torso stability in arabesque": [
        {
            "title": "The ultimate arabesque tutorial: stability and alignment",
            "channel": "My Ballet Coach",
            "url": "https://www.youtube.com/watch?v=xYyyDHYvQpc",
            "source_url": "https://www.youtube.com/watch?v=xYyyDHYvQpc",
            "levels": ["Foundational", "Developing"],
            "stages": ["First time with this cue", "Still inconsistent"],
            "duration_minutes": 12,
            "annotations": [
                ("Look for", "Keep the supporting side organized before asking the working leg to lift."),
                ("Try this", "Think of the ribs staying stacked over the pelvis while the leg lengthens away."),
                ("Check", "If the torso shifts to create height, lower the leg and rebuild the line."),
            ],
        },
    ],
    "Supporting-leg alignment in plié": [
        {
            "title": "Demi-pliés in I, II, V and IV",
            "channel": "Ballet technique reference",
            "url": "https://www.youtube.com/watch?v=K4YqPHHa5i4",
            "source_url": "https://www.youtube.com/watch?v=K4YqPHHa5i4",
            "levels": ["Foundational", "Developing"],
            "stages": ["First time with this cue", "Still inconsistent"],
            "duration_minutes": 10,
            "annotations": [
                ("Alignment cue", "Let the knees travel in the same direction as the toes as you bend."),
                ("Foot cue", "Keep the whole foot connected to the floor instead of shifting into the toes."),
                ("Practice", "Use a smaller range if you cannot keep the pelvis centered and the knee path clear."),
            ],
        },
        {
            "title": "Turnout: find rotation from the hips",
            "channel": "Ballet technique reference",
            "url": "https://www.youtube.com/watch?v=Co3K7VUQjlI",
            "source_url": "https://www.youtube.com/watch?v=Co3K7VUQjlI",
            "levels": ["Developing", "Intermediate"],
            "stages": ["Still inconsistent", "Ready to integrate"],
            "duration_minutes": 12,
            "annotations": [
                ("Avoid", "Do not force the feet farther out if the knees and ankles cannot follow the same line."),
                ("Build", "Practice the amount of turnout you can actively control through the movement."),
                ("Reset", "Choose a smaller first position when the arches begin to collapse or the knees twist."),
            ],
        },
    ],
    "Foot alignment in tendu": [
        {
            "title": "Articulation in tendu | Quick ballet tips",
            "channel": "The Whole Pointe",
            "url": "https://www.youtube.com/watch?v=CqnMJTecRZc",
            "source_url": "https://www.youtube.com/watch?v=CqnMJTecRZc",
            "levels": ["Foundational", "Developing"],
            "stages": ["First time with this cue", "Still inconsistent", "Ready to integrate"],
            "duration_minutes": 8,
            "annotations": [
                ("Pathway", "Keep the foot connected to the floor as it brushes out and returns."),
                ("Length", "Reach through the heel, ball of the foot, and toes to build a longer line."),
                ("Quality", "Avoid crunching the toes or disconnecting the foot from the floor at the end."),
            ],
        },
    ],
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


def load_reference_profile(slug: str) -> dict[str, object]:
    """Load the lesson's reference profile without assuming a reference exists."""
    if not REFERENCE_LIBRARY_PATH.exists():
        return {
            "status": "not_configured",
            "reference_video": None,
            "comparison_metrics": [],
            "description": "Add a teacher-approved reference clip for this lesson.",
            "notes": ""
        }
    payload = json.loads(REFERENCE_LIBRARY_PATH.read_text())
    return payload.get(
        slug,
        {
            "status": "not_configured",
            "reference_video": None,
            "comparison_metrics": [],
            "description": "Add a teacher-approved reference clip for this lesson.",
            "notes": ""
        },
    )


def recommend_video_clips(
    correction_name: str,
    level: str,
    practice_stage: str,
    minutes: str,
) -> list[dict[str, object]]:
    """Rank curated clips against the dancer's current practice context."""
    videos = VIDEO_LIBRARY.get(correction_name, [])
    level_rank = {"Foundational": 0, "Developing": 1, "Intermediate": 2}
    target_level = level_rank.get(level, 0)
    target_minutes = int(minutes.split()[0]) if minutes else 20

    def score(video: dict[str, object]) -> int:
        score_value = 0
        stages = video.get("stages", [])
        levels = video.get("levels", [])
        if practice_stage in stages:
            score_value += 5
        if level in levels:
            score_value += 3
        elif any(level_rank.get(item, 0) <= target_level for item in levels):
            score_value += 1
        duration = int(video.get("duration_minutes", 10))
        score_value += max(0, 2 - abs(duration - target_minutes) // 10)
        return score_value

    return sorted(videos, key=score, reverse=True)
