# Step One Basic Overview

## What we completed

1. Defined the first MVP: analyze one dancer in a short video and provide practice feedback rather than a definitive technique grade.
2. Added `test_video1.mov` and confirmed that pose landmarks could be detected.
3. Built a torso-lean analyzer that measures how far the torso moves from vertical.
4. Created labeled clips from `Full_Training_Vid.mov` for pliés, passé balance, developpé variations, and waltz with pirouettes.
5. Created a local Streamlit dashboard for selecting clips, watching video, viewing annotated frames, and reviewing torso-lean charts.
6. Added the first turnout and lower-body alignment proxy, with clear camera-angle limitations.
7. Added the foundation for dancer-facing visual feedback over the video.

## Current status

The project can organize videos, run the first posture analysis, and display results in a local dashboard. Turnout, knee alignment, square-hip alignment, and sickled-foot detection are the next major analysis features.
