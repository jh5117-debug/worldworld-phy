# Final report: TDW visible-motion v3 200-sample pilot

## Approval

The user requested generation of the 200-sample pilot after accepting the v3 50-sample review set. This run used GPU0-bound `DISPLAY=:8`.

Not run:

- 1k+ TDW generation
- training
- DPO
- VideoGPA `03_train`
- Stage1
- reward calibration
- LingBot rollout
- LoRA/checkpoint save

## Generation

- Profile: `warmup_visible_motion_v3_start0_scene_diverse`
- Plan: `drop:60`, `collision:60`, `roll:40`, `containment:40`
- HDF5 generated: 200 / 200
- Output root: `local_assets/data/physion/generated_v3/`
- Raw HDF5 footprint: about `17G`

## Validation

- HDF5/key validation OK: 200 / 200
- Suitable for warmup: 200 / 200
- Unique scene hashes: 200 / 200
- Duplicate scene hashes: 0
- target_visible_ratio: 1.0 for every sample
- max invisible frames: 0
- too_extreme: 0

Numeric motion diagnostics:

- numeric suitable_for_visible_motion_v3: 116 / 200
- delayed_camera_motion diagnostic: 84 / 200
- too_static diagnostic: 84 / 200
- camera_path_length_total min/avg/max: `0.5518 / 1.1984 / 1.7782`
- camera_path_length_first_8_frames min/avg/max: `0.0552 / 0.1198 / 0.1778`
- background_motion_proxy_total min/avg/max: `0.0192 / 0.0333 / 0.0565`
- background_motion_proxy_first_8_frames min/avg/max: `0.0106 / 0.0254 / 0.0535`

Interpretation:

The pilot is structurally valid and scene-diverse. Numeric early-motion diagnostics still flag the same strafe behavior observed in the 50-sample run; because the user accepted the v3 videos by human review, all 200 samples were converted while retaining those diagnostics for inspection.

## Conversion

- Converted samples: 200 / 200
- target.mp4: 200 / 200
- `use_action=false`: 200 / 200
- dummy `action.npy`: 200 / 200
- conversion errors: 0
- converted footprint: about `37G`

Conversion root:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_200_human_accepted_all/`

## Human Review

Review pack:

`local_assets/reports/human_review/tdw_visible_motion_v3_start0_scene_diverse_200/`

Gallery:

`local_assets/reports/human_review/tdw_visible_motion_v3_start0_scene_diverse_200/video_gallery.html`

## Storage

After generation and all-200 conversion:

- `/home/nvme04` free: about `910G`
- `/home/nvme03` free: about `950G`

## Safety

- No training was run.
- No DPO was run.
- No VideoGPA `03_train` was run.
- No Stage1, reward calibration, or LingBot rollout was run.
- No 1k+ generation was run.
- `local_assets` and generated HDF5 / MP4 / NPY / logs are not committed to Git.

## Next action

Review the 200-sample gallery. If accepted, the next request can be either:

- prepare this 200 set for warmup data indexing; or
- explicitly approve a larger 1k-scale generation.

Do not run 1k automatically.
