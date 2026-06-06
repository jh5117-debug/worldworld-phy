# Final report: TDW visible-motion v3 start0 scene-diverse review set

## Why v3

`warmup_visible_motion_v2` passed pipeline validation, but human review failed it as final warmup data: videos looked too similar, camera motion was still weak, and motion did not appear clearly from frame 0. v3 was created to test stronger start0 motion plus scene diversity.

## v3 design

- Profile: `warmup_visible_motion_v3_start0_scene_diverse`
- Output root: `local_assets/data/physion/generated_v3/`
- Experiment folder: `local_assets/experiments/tdw_visible_motion_v3_start0_scene_diverse_50/`
- Camera motion starts at frame 0 and spans the full 81-frame clip.
- Dolly is excluded.
- Scene diversity uses per-trial scene seeds and validator scene hashes.
- Validation adds early-motion and scene-diversity flags.

## Generation

- Approved resource: GPU0-bound `DISPLAY=:8` for exactly this 50-sample review set.
- Generated HDF5: 50 / 50.
- Validation OK: 50 / 50.
- Planned distribution: drop 15, collision 15, roll 10, containment 10.
- Unique scene hash count: 50 / 50.
- Duplicate scene hash count: 0.

## Motion and acceptance

- Numeric validator accepted for visible-motion v3: 28 / 50.
- Numeric validator rejected: 22 / 50.
- Human review accepted: 50 / 50.
- Too static: 22.
- Too extreme: 0.
- Delayed camera motion: 22.
- target_visible_ratio: 1.0 for all samples.
- max invisible frames: 0.
- camera_path_length_total min/avg/max: `0.5518 / 1.1758 / 1.7782`.
- camera_path_length_first_8_frames min/avg/max: `0.0552 / 0.1176 / 0.1778`.
- background_motion_proxy_total min/avg/max: `0.0209 / 0.0343 / 0.0539`.
- background_motion_proxy_first_8_frames min/avg/max: `0.0132 / 0.0257 / 0.0512`.

Accepted per template:

- drop: 11 / 15
- collision: 7 / 15
- roll: 4 / 10
- containment: 6 / 10

The strict numeric validator rejected every `strafe_left/right_055` and `strafe_left/right_065` sample as too static / delayed. The user manually reviewed the videos afterward and confirmed that all 50 clips are usable. Treat the numeric early-motion flag as a diagnostic warning for this batch, not a hard rejection.

## Human review

Human review pack:

`local_assets/reports/human_review/tdw_visible_motion_v3_start0_scene_diverse_50/`

Gallery:

`local_assets/reports/human_review/tdw_visible_motion_v3_start0_scene_diverse_50/video_gallery.html`

The pack is useful for review and downstream preparation. Based on human review, this v3 50-sample set can be used.

## Conversion

- Converted human-accepted samples: 50 / 50.
- target.mp4 probe completed through the conversion runner.
- `metadata.json` uses `use_action=false`.
- `action.npy` is dummy fallback.

Final conversion root:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50_human_accepted_all/`

## 200 readiness

Ready for an approval request, not automatic execution.

The strict numeric validator did not meet the previous automatic 200-readiness thresholds, but human review accepted the full 50-sample set. A 200-sample pilot can be requested based on human review, but it still requires explicit user approval. Do not run 200 or 1k automatically.

## Safety

- No training was run.
- No DPO was run.
- No VideoGPA `03_train` was run.
- No Stage1, LingBot rollout, or reward calibration was run.
- No 200 / 1k generation was run.
- `local_assets` and generated HDF5 / MP4 / NPY / logs are not committed.

## Next action

Next step:

- write or use a GPU approval request before any 200-sample pilot;
- keep scene-diverse seeds and start0 motion;
- keep the numeric early-motion diagnostics visible in reports, but do not hard-reject this human-accepted 50-sample set.
