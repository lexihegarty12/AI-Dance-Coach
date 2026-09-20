# Self-recorded training clips

Use this folder for consent-free prototype data recorded by the project owner.
Raw video files are ignored by Git and should stay local unless you intentionally
back them up elsewhere.

## Recording checklist

- Record one movement phrase per clip.
- Keep the full body visible, with the camera fixed and the floor visible.
- Start with a neutral standing position for two seconds.
- Record both comfortable and intentionally imperfect repetitions.
- Keep the room, camera height, distance, and lighting consistent for the first set.
- Then record a smaller varied set with a different angle, distance, or tempo.
- Use filenames such as `arabesque_penche_take_001.mp4`.

## Suggested first dataset

Record 10–20 clips each for:

- plié in first;
- plié in fifth;
- arabesque penché;
- one additional movement of your choice.

For each clip, add timestamped notes to `annotations_template.csv`. Label the
moment, the technical cue, and whether the cue is clear or uncertain. These
annotations are coaching labels for future model development; they do not
retrain MediaPipe itself.

## Storage

Keep raw videos and identifying information separate. The derived pose results
and timestamped annotations are the preferred data for future experiments.
