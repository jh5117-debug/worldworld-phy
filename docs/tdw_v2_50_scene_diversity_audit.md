# TDW v2 50 Scene Diversity Audit

## Input

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_50.jsonl`

## Findings

The v2 manifest used 50 distinct top-level `seed` values and a template-aware camera distribution, but it did not explicitly track:

- `scene_seed`;
- `source_config_path`;
- `first_frame_phash`;
- `id_mask_hash`;
- `object_state_summary_hash`;
- `scene_hash`.

The v2 runner also had two design issues that explain the human review result:

1. Camera motion was delayed.
   The per-trial command used `--camera_motion_start 24` and `--camera_motion_end 57`.

2. Non-drop template scene diversity was undermined by template-specific fixed seeds.
   The previous wrapper included fixed non-drop template arguments such as `--seed 328`, `--seed 914`, and `--seed 1`, which could override the per-trial seed depending on upstream argparse behavior.

## Required v3 Diversity Gate

v3 adds explicit plan and validator fields:

- `scene_seed`;
- `source_config_id`;
- `first_frame_phash`;
- `id_mask_hash`;
- `object_state_summary_hash`;
- `scene_hash`;
- `duplicate_scene_hash`.

Acceptance target for a 50-sample review set:

- `unique_scene_hash >= 40`;
- `duplicate_scene_hash_count <= 3`;
- every template has accepted samples;
- not just different camera variants.

## Limitations

This audit records the root-cause evidence available from v2 manifests and command construction. v2 did not emit the full scene-hash metrics; v3 validation is the first run that computes them.
