# Step One Detailed Overview

## Project direction

The project is an AI Dance Coach prototype for ballet practice. It is intended to give understandable, camera-dependent practice cues while supporting—not replacing—a dance teacher. It should not diagnose injury or present a precise-looking measurement as universal truth.

## Work completed

### Scope and data decisions

We narrowed the first version to a single dancer and selected short, labeled video clips rather than analyzing a complete audition video as one movement. We decided to use self-recorded or permission-based reference material instead of downloading professional dancers' videos from the internet. Internet images may inform what to measure, but they should not be treated as unquestioned ground truth or placed in the app without permission.

### Video preparation

The full audition video was inspected as a 9 minute 50 second, 1920 by 1080 recording. The selected clips are stored under `analysis_output/selected_clips/` and include:

- pliés in first;
- pliés in fifth;
- passé balance;
- developpé front;
- developpé to arabesque penché;
- developpé to the side and rond de jambe to arabesque;
- waltz with pirouettes.

Browser-compatible copies were also prepared under `analysis_output/web_clips/` for dashboard playback.

### Pose and posture analysis

The first analyzer uses pose landmarks to estimate torso lean. The metric is the magnitude of the angle between the shoulder center to hip center line and vertical. A value near zero means the torso is close to upright in the camera view; a larger value means more inclination. The result is not automatically good or bad because some ballet movements intentionally use torso inclination.

The first three clips produced these preliminary averages:

| Clip | Average torso lean |
|---|---:|
| Pliés in first | 1.9 degrees |
| Pliés in fifth | 2.0 degrees |
| Passé balance | 0.3 degrees |

These values are baseline observations, not grades or target scores.

### Dashboard

The local Streamlit app is `app.py`. It lets the user select an exercise clip, watch the clip, view an annotated pose frame, and inspect a torso-lean chart. The dashboard is intentionally transparent when an analysis has not been run for a selected clip.

### Current technical limitation

The current MediaPipe setup can encounter a macOS graphics-backend error when rendering a full annotated video. The dashboard and frame-level analysis work, but the visual feedback video still needs a robust rendering path. The next implementation should preserve a usable raw-video view while clearly indicating whether an overlay video exists.

## Lessons for the next phase

The system should compare movement against a labeled position or exercise, not a single universal posture. Plié, passé, arabesque, penché, and pirouette phrases require different expectations. Reference ranges should be created from consistent camera views and reviewed by an experienced dancer or instructor.
