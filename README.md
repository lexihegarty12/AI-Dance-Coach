# AI Dance Coach: first technique analyzer

This first vertical slice analyzes one dancer and measures torso lean as a
camera-dependent posture proxy. It is a practice cue, not a ballet grade or
medical assessment.

## Run it

The project uses a local virtual environment:

```bash
.venv/bin/python -m pip install -r requirements.txt
mkdir -p models
curl -L "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task" -o models/pose_landmarker_lite.task
.venv/bin/python src/analyze_technique.py test_video1.mov
```

Results are written to `analysis_output/`:

- `technique_results.csv` contains one row per video frame.
- `annotated_sample.jpg` shows detected landmarks and the torso-lean value.

## Dashboard

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

The dashboard lets you choose a labeled clip, watch it, view the annotated
frame, and inspect the torso-lean chart. The turnout panel is intentionally
labeled as a camera-dependent proxy.

To render dancer-facing visual feedback for a clip:

```bash
.venv/bin/python src/render_feedback_video.py \
  analysis_output/selected_clips/plies_first.mp4 \
  --output-dir analysis_output/plies_first_results
```

The rendered video highlights the detected body and displays a visual cue when
torso lean exceeds the current alert threshold. This is a practice prompt, not
a definitive technique judgment.
