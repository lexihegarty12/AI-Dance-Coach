# AI Dance Coach Project Plan

## Purpose

Build and deploy a Python-first web application that analyzes a short ballet rehearsal video and gives understandable, non-diagnostic feedback on selected technique proxies and group synchronization. The product should support, not replace, a dance teacher or coach.

This plan is designed to produce two useful outcomes:

1. A functional semester project that satisfies the course milestones.
2. A credible poster demonstration for Cal Poly's Fall AI Convening on October 22, 2026.

## Working product definition

### Target user

Ballet students and small dance teams practicing outside class who want immediate, specific feedback when an instructor is unavailable.

### Minimum viable product

The first version should accept one short uploaded video, extract body landmarks frame by frame, calculate a small number of interpretable metrics, and return visual and written feedback.

The MVP should analyze:

- posture proxy: torso lean and shoulder/hip alignment;
- arm placement proxy: selected shoulder-elbow-wrist angles;
- lower-body alignment proxy: hip-knee-ankle relationships;
- balance proxy: torso/hip sway during a selected phrase;
- synchronization: timing and movement similarity across dancers when multiple people are visible.

The application should show an annotated video or frame samples, a metric summary, a simple time-series chart, and three prioritized practice suggestions.

### Explicitly out of scope for the MVP

- claiming to grade ballet technique like a certified instructor;
- diagnosing injury, physical limitation, or medical condition;
- identifying individual people or recognizing faces;
- training a new foundation pose model from scratch;
- supporting every ballet position, leap, turn, and camera angle;
- real-time camera coaching;
- production-scale storage of personal rehearsal videos.

Turnout should be described as a 2D camera-dependent proxy, not a definitive measurement. True turnout assessment needs multiple camera angles and expert validation.

## Recommended technical approach

### Architecture

Use a small, understandable pipeline rather than a large custom model:

`Upload video -> validate and temporarily store -> sample frames -> detect pose landmarks -> normalize landmarks -> calculate metrics -> create charts/overlays -> generate coaching text -> display and delete video`

### Recommended stack

| Layer | Recommendation | Why |
|---|---|---|
| Language | Python 3.11 or newer | Fastest path for computer vision, data analysis, and deployment |
| Web app | Streamlit for MVP | Minimal frontend code and easy demo deployment |
| Video | OpenCV and FFmpeg | Read video metadata, sample frames, render overlays, handle common formats |
| Pose estimation | MediaPipe Pose Landmarker | Pretrained human-pose model that is practical on ordinary hardware |
| Numerical analysis | NumPy | Vectorized geometry and time-series calculations |
| Data handling | pandas | Metric tables, summaries, and exportable evaluation data |
| Charts | Plotly | Interactive metric-over-time charts in Streamlit |
| Optional signal processing | SciPy and librosa | Smoothing, cross-correlation, and optional beat/onset timing |
| Persistence | SQLite or local JSON during development | Store experiment metadata without introducing a large backend |
| Optional API split | FastAPI | Add only if a separate frontend or mobile client becomes necessary |
| Coaching language | Template rules first; optional LLM second | Keeps feedback grounded in measured values and reduces hallucination risk |
| Testing | pytest | Unit-test geometry and metric calculations |
| Packaging | uv or pip plus requirements.txt | Reproducible setup for classmates and deployment |
| Deployment | Streamlit Community Cloud or a comparable managed host | Fastest route to a shareable demonstration |

Start with Streamlit. Do not build a React frontend, database service, authentication system, or custom deep-learning training loop until the core analysis works.

## Data required

### Data for the MVP

1. **Input videos**: 5-20 second clips recorded with a fixed camera, full body visible, good lighting, and one or more dancers.
2. **Video metadata**: frame rate, resolution, duration, camera angle, number of dancers, and whether audio is present.
3. **Pose landmark output**: frame number, timestamp, landmark name, x/y/z coordinates, visibility confidence, and person/track identifier if multiple people are detected.
4. **Reference examples**: a small set of clips or still images representing the intended movement and camera setup. These are for comparison and demonstration, not a universal standard of perfect ballet.
5. **Expert feedback**: a dance teacher or experienced dancer should review a sample of generated outputs and mark whether each suggestion is reasonable, unclear, or wrong.
6. **User-test responses**: task completion, perceived usefulness, clarity, confidence, and what the user would change.

### Suggested data schema

`videos.csv` or a database table:

- `video_id`
- `session_id`
- `duration_seconds`
- `fps`
- `width`
- `height`
- `camera_view`
- `dancer_count`
- `movement_label`
- `consent_status`
- `consent_scope` (private analysis, model development, public demo)
- `participant_id` (pseudonymous; stored separately from contact information)
- `withdrawal_requested_at`
- `retention_expiry`

`landmarks.parquet` or database table:

- `video_id`
- `frame_index`
- `timestamp_seconds`
- `person_id`
- `landmark_name`
- `x_normalized`
- `y_normalized`
- `z_relative`
- `visibility`

`metrics.csv`:

- `video_id`
- `timestamp_seconds`
- `metric_name`
- `metric_value`
- `confidence`
- `camera_sensitivity_note`

`feedback.csv`:

- `video_id`
- `metric_name`
- `system_feedback`
- `expert_rating`
- `user_rating`
- `comment`

### Data collection plan

Begin with synthetic or self-recorded test clips so the pipeline can be developed without collecting identifiable student data. Then collect a small, consented evaluation set:

- 10-20 short clips for engineering tests;
- 5-10 clips with intentionally varied camera distance, lighting, and movement quality;
- 3-5 expert-reviewed clips for feedback validation;
- peer testing with no video retention after the test session unless explicit consent is given.

Do not download random dancers' videos from the internet for training or evaluation. Use consented, licensed, or self-created data.

### Ethical data-collection requirements

Treat dancers as participants and obtain informed, voluntary consent before recording. The consent process must explain, in plain language:

- what is collected: raw video, derived pose landmarks, timestamps, and technical annotations;
- how it may be used: private analysis, model development, evaluation, or public demonstration;
- that the system provides camera-dependent practice cues, not grades, diagnoses, or definitive judgments;
- how long data will be retained, who can access it, and how participants can ask questions or request deletion.

Use separate opt-in permissions for model development and public demo display. Do not rely on consent obtained under pressure from a teacher, employer, audition, or grading relationship. Assign pseudonymous participant IDs, store consent/contact information separately from video, restrict access, and delete raw video on a documented schedule when derived landmarks are sufficient.

Participants must be able to withdraw without penalty. If a participant withdraws, remove their raw video and derived records where practical and document what was deleted. For minors, obtain guardian permission and the dancer's assent, and follow any school, studio, or institutional review requirements.

Expert reviewers should label feedback as acceptable, needs attention, or unclear, rather than treating a cue as an objective ballet score. Training and test splits must be separated by dancer and session—not merely by individual frames—to test whether the model generalizes beyond people it has already seen. The project should maintain a short dataset record describing consent scope, retention, known camera limitations, and intended use.

## How the analysis works

### Landmark processing

For each frame:

1. Detect pose landmarks and confidence scores.
2. Drop or interpolate frames with low visibility.
3. Normalize coordinates to the body, such as shoulder width or hip width, so distance from the camera matters less.
4. Smooth noisy trajectories with a moving median or Savitzky-Golay filter.
5. Segment the clip into a selected movement phrase or analyze the full clip.

### Metric examples

- **Torso lean**: angle between the shoulder-center-to-hip-center vector and the vertical axis.
- **Shoulder or hip alignment**: difference in height and angle between the left and right landmarks.
- **Arm placement**: elbow and wrist angles relative to shoulders and torso.
- **Knee alignment**: normalized horizontal offset between knee and ankle or knee and hip, clearly labeled as a camera-view proxy.
- **Balance**: variation in torso-center or hip-center position over time during a stable phrase.
- **Unison**: align dancers' normalized landmark trajectories using cross-correlation or dynamic time warping, then report timing offset and movement similarity.

For each metric, return a value, a confidence score, and a limitation note. Never show a precise-looking score without explaining that it depends on camera setup and pose-detection confidence.

### Coaching feedback

Use a rules layer first. For example:

- If torso lean exceeds a selected threshold for a sustained period and confidence is high, say: “Your torso leans forward during this section. Try checking your ribcage-over-hips alignment.”
- If synchronization lag is consistent, say: “The left side begins this phrase slightly after the group. Try marking the preparation count together.”

An optional language model can rewrite structured, already-measured findings into friendly wording. It should receive only JSON metrics and constraints, not raw video, and it must not invent observations. Keep a deterministic template fallback so the app still works without an API key.

## Evaluation and success criteria

### Technical acceptance criteria

- A user can upload a supported video without crashing the application.
- The system reports clear errors for unsupported files, no visible person, multiple people outside the supported range, or low confidence.
- A typical 10-second clip completes within a reasonable demo wait time.
- At least 80% of test clips produce landmarks and a results page.
- The app displays raw measurements, confidence, and limitations alongside recommendations.
- Uploaded files are deleted after analysis or after a clearly stated retention period.

### User and model evaluation

- At least three dancers or classmates complete a test task.
- At least one experienced dancer or instructor reviews a sample of outputs.
- Record whether feedback is perceived as clear, actionable, and trustworthy.
- Report failure cases, such as side views, occlusion, poor lighting, loose clothing, or multiple dancers crossing paths.

### Poster-worthy evidence

The poster should show:

- the user problem;
- the analysis pipeline;
- one annotated frame and one metric chart;
- a short table of test clips and completion rate;
- user/expert feedback results;
- limitations and responsible-AI choices;
- a QR code linking to the deployed demo or a recorded walkthrough.

Do not present the system as clinically accurate or as a replacement for teachers.

## Project schedule and deadlines

The dates below combine the course guide's Week 3/6/10/12/13 milestones with the fixed event deadlines provided in the announcement. Course week dates should be confirmed against the official class calendar.

| Date | Milestone | Deliverable | Definition of done |
|---|---|---|---|
| Sep 18, 2026 | Scope lock | One-page MVP brief | User, core workflow, metrics, risks, and out-of-scope items are agreed |
| Sep 19 | Application materials | Draft poster abstract and application responses | Clear problem, AI method, expected impact, and responsible-AI framing |
| Sep 20 | Data and consent setup | Data dictionary, consent language, sample-video checklist | Test data can be collected and labeled safely |
| Sep 21 | MVP technical skeleton | Git repo structure, local app, upload screen, requirements | App launches locally and accepts a test video |
| Sep 22 | Fixed deadline | Submit Fall AI Convening application | Application submitted by Tuesday, September 22 |
| Sep 23-25 | Pose pipeline | Landmark extraction notebook/script | At least one clip produces landmark data and a plotted skeleton |
| Sep 26-29 | Core metrics | Posture, arm, lower-body, balance, and confidence calculations | Metrics work on known test cases and have unit tests |
| Sep 30-Oct 2 | Results UI | Charts, annotations, error messages, and feedback templates | A user can upload a clip and understand the results |
| Oct 3 | Course Week 6 target | Working MVP demonstration | Primary workflow works end to end, even if rough |
| Oct 4-8 | Synchronization | Multi-dancer handling and timing similarity | One supported group clip produces an interpretable timing result |
| Oct 9-11 | Deployment | Public or instructor-accessible demo URL | Another person can use the app without local setup |
| Oct 12-14 | User testing | Test protocol and feedback form | At least three users complete the same task and feedback is recorded |
| Oct 15-16 | Poster v1 | Poster draft with evidence and limitations | A reviewer can understand the project in under two minutes |
| Oct 17-18 | Refinement | Fix highest-impact usability and accuracy issues | Critical bugs closed; demo path rehearsed |
| Oct 19 | Poster v2 and demo freeze | Final content, QR code, backup screen recording | Poster and live demo are stable |
| Oct 20-21 | Presentation rehearsal | 60-90 second explanation plus 3-minute demo | Can explain problem, method, evidence, limitations, and impact |
| Oct 22 | Fixed event deadline | Fall AI Convening poster presentation | Present the project and collect questions/contacts |
| Course Week 10 | Peer testing | Test results and revision list | Peer feedback is documented and prioritized |
| Course Week 12 | Final product | Deployed final application | Functional, polished, documented, and ready to show an employer |
| Course Week 13 | Final presentation | Final class presentation | Demonstrate and explain the final product |

## Weekly work breakdown

### Phase 1: Define and de-risk

Decide exactly which movement and camera setup the MVP supports. Write the limitations before building. Create a small test set and prove pose extraction works.

### Phase 2: Build the vertical slice

Build one complete path: upload one short video, extract landmarks, calculate one metric, show one chart, and produce one grounded suggestion. This is more valuable than partially building ten features.

### Phase 3: Add metrics and group analysis

Add the remaining selected metrics one at a time. For group synchronization, start with two dancers in a fixed camera view and a simple movement phrase. Add more complexity only after the basic case is reliable.

### Phase 4: Deploy and test

Deploy early, test from a second device, document latency and failure cases, and collect structured feedback. Prioritize fixes that improve clarity and successful completion of the main workflow.

### Phase 5: Poster and final polish

Freeze the measurement definitions, capture clean screenshots, summarize evidence honestly, and rehearse the demo using a backup video and screenshots in case the live app or network fails.

## Repository structure

```text
ai-dance-coach/
  app.py
  requirements.txt
  README.md
  src/
    video_io.py
    pose_pipeline.py
    metrics.py
    synchronization.py
    feedback.py
  tests/
    test_metrics.py
    test_video_validation.py
  data/
    README.md
    sample_metadata.csv
  notebooks/
    01_pose_exploration.ipynb
    02_metric_validation.ipynb
  assets/
    sample_frames/
    poster/
```

Keep raw videos out of Git. Use `.gitignore` and store only synthetic, consented, or redacted demo assets in the repository.

## Risk register

| Risk | Likely effect | Mitigation |
|---|---|---|
| Pose model fails on ballet poses or occlusion | Missing or noisy feedback | Restrict camera setup, show confidence, add clear failure states, and test edge cases |
| Turnout is overinterpreted | Misleading technique advice | Label it as a 2D proxy and remove it if validation is weak |
| Multi-person tracking swaps identities | Incorrect synchronization result | Start with two dancers, fixed positions, and a supported camera view |
| Scope grows too quickly | No stable demo | Freeze MVP and defer real-time, mobile, custom training, and broad movement coverage |
| LLM invents coaching claims | Unsafe or untrustworthy feedback | Use structured metrics, templates, constraints, and a no-LLM fallback |
| Sensitive video is retained | Privacy risk | Consent, minimal collection, automatic deletion, no face recognition, and no raw video in logs |
| Deployment is unreliable | Failed poster demo | Record a backup walkthrough and keep static screenshots locally |

## Application draft for the Fall AI Convening

### Working title

AI Dance Coach: Pose-Based Feedback for Ballet Practice and Group Synchronization

### Short project description

AI Dance Coach is a Python-based web application that analyzes short ballet rehearsal videos and translates computer-vision measurements into understandable practice feedback. The prototype uses pose landmarks to estimate camera-dependent proxies for posture, arm placement, lower-body alignment, balance, and timing similarity between dancers. It visualizes movement patterns over time and provides prioritized suggestions while clearly communicating confidence and limitations. The system is designed to support dance teachers and students, not replace expert instruction or provide medical advice.

### Why it matters

Dancers often practice outside class without immediate access to a teacher. The project explores how responsible, human-centered AI can make practice more intentional by giving users a repeatable way to review movement timing and alignment. It also demonstrates an interdisciplinary application of analytics, computer vision, and user-centered product design.

### Responsible-AI statement

The prototype uses consented or self-created videos, avoids identity recognition, minimizes retention of raw video, reports confidence and camera sensitivity, and treats its outputs as practice cues rather than authoritative judgments. Data collection uses explicit, purpose-specific consent, pseudonymous participant IDs, documented retention and deletion, and separate permission for public demonstration. Expert and user feedback are part of the evaluation.

## Immediate next actions

1. Confirm the exact course calendar dates for Weeks 3, 6, 10, 12, and 13.
2. Submit the event application by September 22 using the draft above and any required personal/course details.
3. Record an initial self-recorded dataset using `data/self_recorded/README.md` and `annotations_template.csv`.
4. Build the one-video vertical slice before adding group synchronization.
5. Review the first five feedback outputs and mark which cues are clear, useful, or wrong.
