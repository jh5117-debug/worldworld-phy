# TDW v5 200 Data Integrity Audit Report

Date: 2026-06-09

## Scope

Manifest audited:
`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`

Audit output:
`local_assets/experiments/exp_tdw_v5_200_lingbot_warmup_gate/audit/audit_report.json`

## Result

- Total samples: 200
- Valid samples: 200
- Invalid samples: 0
- Video probe pass: 200 / 200
- Duplicate sample ids: 0
- Ready for dataloader: yes

## File And Shape Checks

- `target.mp4`: exists and probe-readable for all 200
- `image.jpg`: present and readable
- `poses.npy`: `[81, 4, 4]` for all 200
- `intrinsics.npy`: `[81, 4, 4]` for all 200
- `action.npy`: `[81, 4]` for all 200
- computed action norm: zero for audited samples
- metadata `use_action=false`: required and passed
- prompts: non-empty

## Distribution

- Templates: drop 60, collision 60, roll 40, containment 40
- Camera variants:
  - `orbit_left_72`: 60
  - `orbit_right_64`: 30
  - `strafe_left_180`: 30
  - `orbit_right_60`: 40
  - `orbit_left_44`: 40

## Note

The first audit attempt failed because the server did not have `ffprobe` in PATH. The audit script now falls back to OpenCV `VideoCapture`, and the corrected audit passes 200 / 200.
