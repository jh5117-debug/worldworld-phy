# v14 Real-Energy Blocker Retry Summary

Generated: `2026-07-08T03:30:22`

## Decision

`REAL_ENERGY_CALIBRATION_BLOCKED_FORWARD_TIMEOUT`

This retry did not change the v14 DPO decision. The v14 DPO recipe remains `DPO_RECIPE_NOT_FOUND_V14`, with `NO_SCALE`, `NO_S16_S32`, and `NO_TRAIN400`.

## What Was Tried

1. Original S_pass real-energy retry:
   - Command used `cam_physgeo.dpo.full_real_energy_audit run-shard` with `--limit 1` on physical GPU4.
   - Output: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_s_pass1_full_audit/shard_00_of_01.csv`.
   - Result: one failed row due to prefix5 schema/assets problems.
   - Error: missing loss/reward frame indices and missing prefix/winner/loser video fields or files.

2. Asset-complete adapter attempt:
   - Scanned v14 S_pass, stratified100, synthetic_controlled, and canonical ready500.
   - Scan output: `reports/dpo_utility_calibration_v14/blocker_retry/asset_complete_prefix5_scan.csv`.
   - No existing row was directly compatible with `Prefix5DpoDataset` because current manifests use mixed/nested schemas and many local video paths are absent after cleanup.
   - Reconstructed one synthetic controlled pair locally under `local_assets/dpo_utility_calibration_v14/blocker_retry/` using GT full video plus loser future video.
   - Adapter summary: `reports/dpo_utility_calibration_v14/blocker_retry/asset_complete_prefix5_adapter_summary.json`.
   - The adapted one-pair manifest passed `prefix5_schema_errors` with no schema errors.

3. Environment repair:
   - Conda `python3` is Python 3.13 and failed on transformers/huggingface-hub version conflict.
   - `/usr/bin/python3` imported `cam_physgeo.dpo.full_real_energy_audit`, `cam_physgeo.dpo.lingbot_fast_energy`, and `stage1_components` successfully.
   - Re-ran the one-pair real-energy smoke with `/usr/bin/python3`, `CUDA_VISIBLE_DEVICES=4`, and a 900 second timeout.

## Final Retry Result

- Command output: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_asset_complete_onepair_usrbin_stdout.txt`.
- Exit code: `124` from timeout.
- It successfully passed:
  - prefix5 schema validation;
  - Python import environment conflict;
  - LingBot shard loading warnings for all 16 safetensors shards;
  - entry into VAE path (`wan/modules/vae2_1.py`).
- It did not write a real-energy CSV/JSONL row before the 900 second timeout.

## Current Exact Blocker

Real LingBot energy calibration is blocked at the one-pair energy/VAE forward path: after schema/env/shard loading are repaired, the first pair still does not complete within 900 seconds. This prevents all500/S_pass/rollout real-energy calibration from being claimed.

## Implication For DPO

This does not produce a valid DPO recipe. Existing v14 schemes E09/E10 have scalar training signal but fail true V2V-5 video audit. DPO cannot proceed to S16/S32/train400 until a recipe passes training signal, checkpoint video, metrics, and Codex visual audit.

## Safe Next Action

Instrument `LingBotFastDpoEnergy` / VAE encode / energy forward with per-stage heartbeat and row-level timeout, or precompute/cache latents for the energy audit. Do not run more DPO training until the visual/metric mismatch blocker is addressed.
