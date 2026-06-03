# Final Report: TDW Generation v2 Mild Smoke

## 1. Current Status

- Intended remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_fixed_noise_diagnostic_work/world_model_phys_tdw_generation_v2_prd_work/world_model_phys_tdw_generation_v2_mild_smoke_work`
- Branch: `physion-tdw-generation-v2-mild-smoke`
- Base branch: `physion-tdw-generation-v2-prd`
- Correct remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Training: not run
- DPO: not run
- VideoGPA 03_train: not run
- Stage1: not run
- LingBot rollout: not run
- Reward calibration: not run
- `local_assets`: not committed
- Data/weights: no assets were moved or deleted

Remote SSH was intermittent during syncing, but the remote code was eventually updated and the actual TDW generation gate was executed. It stopped before Unity because the TDW display appears GPU0-bound.

## 2. GPU Usage

No new TDW/Unity generation was launched. The observed H20 process audit showed GPUs 6/7 idle, while an existing Xorg process for TDW display `:8` was configured with `tdw-xorg-gpu0.conf`. Because this round only allows GPU6/7 for smoke tasks, actual TDW generation on `:8` is blocked until display routing is fixed or user approval is given.

A GPU/display approval request was written:

- `docs/gpu_usage_approval_request.md`

50-sample generation was not run because 1-sample was not run and because resource/GPU routing is unresolved.

## 3. Mild Camera Patch

Implemented explicit `camera_set: warmup_mild`.

Allowed variants:

- `orbit_left_12`
- `orbit_right_12`
- `strafe_left_025`
- `strafe_right_025`
- `dolly_in_010`
- `dolly_out_010`

Banned warmup terms:

- `lookaway`
- `offscreen`
- `relative_yaw_180`
- `relative_lookaway`
- `reobserve`
- `occluder`
- `extreme`

Upstream mapping:

- orbit variants map to `camera_motion=orbit` with `camera_orbit_degrees=+/-12`;
- strafe variants map to `camera_motion=strafe` with `camera_strafe_distance=+/-0.25`;
- dolly variants map to the upstream orbit/radius-delta path with `camera_radius_delta=+/-0.10`.

The wrapper does not modify the upstream TDW runner. It generates a runtime wrapper that replaces the upstream `CAMERA_VARIANTS` list in memory with the mild-only list and then calls upstream `main()`.

## 4. Generation

| Stage | Status | Notes |
|---|---|---|
| plan dry-run | passed | 10 planned trials, no stress/reobserve variants |
| 1-sample actual | blocked | remote gate returned `status=blocked`; TDW display appears GPU0-bound; current task allows only GPU6/7 |
| 10-sample smoke | skipped | requires 1-sample actual validation first |
| 50-sample validation | skipped | requires 10-sample pass and resource approval |

Generated count: 0.

Success count: 0.

Reject count: 0.

## 5. Validation

HDF5 validation was run after the blocked gate and found:

- HDF5 count: 0
- validation ok count: 0
- suitable for warmup: 0

No contact sheet was generated because there was no generated sample.

Expected validation once generation is allowed:

- RGB / `_img`;
- `_depth`;
- `_id`;
- camera pose / position / aim;
- projection or camera matrix;
- object state;
- frame count and resolution;
- target visibility ratio;
- foreground disappearance;
- camera yaw/translation magnitude;
- contact sheet.

## 6. LingBot Conversion

Skipped because no accepted generated samples exist yet.

When enabled, accepted samples should convert to:

- `image.jpg`;
- `target.mp4`;
- `poses.npy`;
- `intrinsics.npy`;
- `prompt.txt`;
- `metadata.json`;
- optional `depth.npy`;
- optional `id_mask.npy`;
- dummy `action.npy`;
- `use_action=false`.

## 7. Video Deliverables

Existing video deliverables remain under:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

No new TDW v2 warmup videos were added. The old clean GT sample remains a stress/test example because the camera motion is too strong and the foreground can disappear.

## 8. Next Steps

1. Fix or approve TDW display/GPU routing so actual generation can use GPU6/7 or an explicitly approved display.
2. Run 1-sample `warmup_mild` actual smoke.
3. Validate HDF5 completeness, camera metadata, target visibility, and contact sheet.
4. Only if 1-sample passes, run 10-sample smoke.
5. Only if 10-sample passes and resource use is light/approved, consider 50-sample validation.
6. After staged generation succeeds, use accepted `warmup_mild` samples for later LingBot-Fast camera warmup.
7. Later, after enough data and stable reward, use reward-selected top/bottom pairs for DPO.

No real training is allowed yet. Before any large GPU job, ask the user first.
