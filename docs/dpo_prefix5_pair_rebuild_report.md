# DPO Prefix-5 Pair Rebuild Report

Updated: 2026-06-27 03:24:08

## Input

- Old pair file: `local_assets/overnight_quant_lora_dpo_20260624_overnight_test/anchored_pairs/anchored_dpo_probe_pairs.jsonl`
- Old prefix status: I2V-1 / first-image condition. `prefix_len` was missing for all 50 old pairs.

## Output

- New prefix5 manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Prefix5 pair count: `50`
- Valid pair count: `50`
- Contact sheets: `reports/dpo_prefix5_pair_visual_audit/pair_contact_sheets`
- Pair audit CSV: `reports/dpo_prefix5_pair_visual_audit/pair_audit.csv`
- Pair audit JSONL: `reports/dpo_prefix5_pair_visual_audit/pair_audit.jsonl`

## Schema Guarantees

Every rebuilt pair sets:

- `condition.prefix_len = 5`
- `condition.prediction_start_frame = 5`
- `condition.prefix_video_path` points to a 5-frame clean prefix clip
- `winner.future_video_path` points to frames 5-80 of clean GT future
- `loser.future_video_path` points to frames 5-80 with a controlled corruption
- `loss_frame_indices = [5..80]`
- `reward_frame_indices = [5..80]`
- `same_prefix = true`
- `same_prompt = true`
- `same_poses = true`
- `same_intrinsics = true`

Frame validation passed: all prefix clips have 5 frames; all winner/loser future clips have 76 frames.

## Corruption Type Distribution

- background_drift: 8
- freeze_foreground: 7
- nonrigid_background_warp: 7
- object_deformation: 7
- object_identity_change: 7
- reobserve_mismatch: 7
- wrong_camera_motion: 7


## Invalid Reason Stats

none

## DPO Decision

From the pair-schema perspective, the rebuilt pairs are now valid V2V-5 anchored pairs. However, real DPO still should not start until the LingBot-Fast winner/loser flow-matching energy backend is callable and BF16 DDP preflight passes on that real backend.
