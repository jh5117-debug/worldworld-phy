# TDW v5 Stage A Rollout Compare Report

Date: 2026-06-10

## Status

Real rollout was not run in this turn.

Remote dry-run passed on H20:

- selected conditions: 4;
- template distribution: drop 1, collision 1, roll 1, containment 1;
- camera variants: `orbit_left_72`, `strafe_left_180`, `orbit_right_60`, `orbit_left_44`;
- adapter checkpoint path resolved;
- no video generation was started.

## What Changed

Added a real adapter inference path:

- `cam_physgeo/eval/run_inference.py` can now load the Stage A adapter checkpoint;
- it accepts only `cam_physgeo_runtime_lora_adapter_v1`;
- it injects the saved LoRA modules into LingBot-Fast before `pipe.generate`;
- it does not train, save, or modify base weights.

Added rollout wrapper:

- `cam_physgeo/eval/rollout_compare_base_adapter.py`;
- selects balanced conditions from a manifest;
- runs base and Stage A adapter variants;
- writes per-sample metadata and contact sheets.

## Why It Did Not Run

The requested 12 conditions imply 24 LingBot-Fast generations. Historical small Fast rollout work used long autoloop runs; this 81-frame base-vs-adapter comparison is expected to risk exceeding the 12-hour threshold.

## Next Approval

Approve a bounded rollout smoke, preferably starting with 4 conditions, one per template, before 12-condition expansion.

Dry-run selected sample IDs:

- `tdw_v3_00000_drop_orbit_left_72_seed22000_0000`
- `tdw_v3_00093_collision_strafe_left_180_seed22093_0000`
- `tdw_v3_00145_roll_orbit_right_60_seed22145_0000`
- `tdw_v3_00161_containment_orbit_left_44_seed22161_0000`
