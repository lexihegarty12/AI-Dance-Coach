# Technique dataset

`technique_data_cleaned.csv` is the normalized working copy of the original
`technique_data(Sheet1).csv`. The original file is preserved unchanged.

## Fields used for the first baseline

- `file_name`: exact filename under `raw_dance_vids/`.
- `dancer_id`: pseudonymous dancer identifier.
- `recording_session`: session parsed from the filename. Keep whole sessions together when creating train/test splits.
- `movement_group`: normalized movement group: `plie`, `tendu`, `plie_and_tendu`, or `other`.
- `camera_view`: normalized view: `front`, `side`, or `45_degree`.
- `overall_label`: `good`, `bad`, or `needs_review`.
- `primary_correction_category`: one main issue category where the notes support it.
- `review_status`: whether the row is ready for baseline use.

## Current review flags

- `good_example`: a good example without coaching notes.
- `good_with_coaching_notes`: marked good, but contains technique notes. Keep separate from clean positive examples until reviewed.
- `issue_labeled`: marked bad with a usable issue category.
- `needs_review`: missing a specific issue label or otherwise ambiguous.

Before building classifications, review the `needs_review` row and decide whether
the good videos with coaching notes are clean examples or should receive a
specific issue label.

## First baseline

`technique_data_baseline.csv` is the lighter working set for the first product.
It does not require good/bad labels. It keeps the original coaching notes and
adds provisional tags only for two target cues:

- plié knee tracking
- tendu foot alignment

These tags are automatically inferred from the notes. Rows marked
`reference_candidate` have no correction note and may be useful as comparison
clips, but they are not assumed to be perfect. `out_of_scope` rows are retained
but excluded from the first plié/tendu baseline.
