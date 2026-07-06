# EXP: DPO Utility Calibration and Latent Monitor v14

## Current Status

- Canonical repaired ready500 manifest exists.
- v13b failed to find a valid DPO recipe.
- `S07_linear_winner_detached` had the best winner-positive training signal, but failed the checkpoint metric gate because VBench temporal_flickering worsened.
- Most v13b schemes had preference utility around 1e-4 and DPO loss near 0.693.
- Current blocker is utility / gap scale, not data availability.
- This run uses only H20 physical GPU4 and GPU5.
- No large DPO is allowed.

## Problem

DPO preference training is not yet entering a useful optimization regime. Likely failure modes include signal dilution from energy reduction, too-small beta, policy/reference closeness, mild synthetic pairs, full-future mask dilution, win/lose gap noise-scale mismatch, uncalibrated normalized gaps, and unvalidated V-JEPA / VideoREPA / TRD latent relation signal.

## Hypothesis

Per-sigma/per-pair normalization, empirical beta calibration, local/time masks, pair-source weighting, and latent relation monitoring can identify a usable preference objective or prove the exact blocker before any scale.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_top50_demo_repaired.jsonl`
- `manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl`
- `manifests/dpo_v12b_subsets/s_fail_winner_anchor.jsonl`
- `manifests/dpo_v12b_subsets/val_video_4.jsonl`
- `manifests/dpo_v13b_subsets/s4_pass.jsonl` if present
- `manifests/dpo_v13b_subsets/s8_pass_expand.jsonl` if present
- `manifests/dpo_v13b_subsets/s16_confident.jsonl` if present
- `manifests/dpo_v13b_subsets/s4_local_mask.jsonl` if present
- v12b warm-start LoRA: `local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/winner_anchor_repeat_L0_camera_r4_step020_lora_state.pt`

## GPU Policy

Allowed physical GPUs: 4 and 5. Forbidden physical GPUs: 0, 1, 2, 3, 6, 7. Every GPU command must set `CUDA_VISIBLE_DEVICES=4` or `CUDA_VISIBLE_DEVICES=5`. Two single-GPU jobs may run in parallel. DDP is not used. Unknown GPU processes are never killed.

## Phase A: Pair Inventory

Build v14 subsets: all500, s_pass, s_fail, rollout_only, synthetic_controlled, stratified100, and local_mask. Report source, failure, reward-margin, visual-audit, local-mask, rollout, and synthetic distributions.

## Phase B: Offline Energy / Utility Calibration

For required subsets, compute real LingBot energy when runtime allows: raw energies, raw gaps, winner/loser directions, `u_raw`, `u_log`, `u_z`, `u_mad`, per-token/reduction variants, local-mask variants, sigma/timestep/bin metadata, and source/failure/reward metadata. Rows must append incrementally and failed rows must record status/error_reason. No fake energy.

## Phase C: Beta / Lambda / Loss Response Sweep

Sweep beta from 0.01 to 1000 for raw/log/z/MAD/local utilities. Report logit, DPO loss response, gradient scale, near-zero/effective/saturation ratios, and recommended utility/beta/clip/pair filter. Must explain why beta=0.1 was ineffective.

## Phase D: V-JEPA / VideoREPA / TRD Latent Monitor

Audit local V-JEPA / VideoREPA / VideoMAE / DINOv2 / CLIP-video / feature-cache availability. Do not download models. If no backend exists, write `LATENT_MONITOR_BLOCKED`. If backend exists, compute winner/loser distance margins and correlation with reward/visual audit. Monitor only, no training.

## Phase E: Normalization / Regularization Design

Recommend per-token/local/sigma-bin reduction, log/z/MAD normalization, empirical beta, clipped/detached loser handling, winner protection, local mask rules, and v15 latent auxiliary preconditions.

## Phase F: 10 Calibrated Objective Schemes

Only after `recommended_dpo_scale.json` exists. Candidate schemes E01-E10 cover raw/log/z calibrated winner-detached, normalized winner-only, clipped loser alpha 0.02/0.05, linear best utility, local time mask, source-weighted rollout priority, and L2 camera-temporal calibrated. Each scheme is <=200 steps, starts on S4/S8, and never exceeds S16 in this round.

## Checkpoint Video + Metrics Gate

Only training-signal-pass schemes get true V2V-5 checkpoint evaluation. Required: PSNR, SSIM, LPIPS, real FVD smoke if available, VBench temporal_flickering, PhysGeo, and Codex visual audit. No image-only or prefix_len=1 fallback.

## Success Gate

Offline calibration covers ready500 + S_pass + rollout/synthetic/local subsets; beta/u distribution is reported; best reduction and normalization are identified; latent monitor passes or reports exact blocker; 10 schemes are attempted or skipped with justified blockers; at least one scheme passes training + video + metrics to declare recipe found; no forbidden GPU use.

## Failure Gate

Missing all-pair statistics; fake VJEPA/TRD/FVD/VBench values; missing visual audit for promising checkpoint; scheme selected by loss only; any forbidden GPU use; large DPO/train400 starts accidentally.

## What Is Not Run

No train400, no large DPO, no S32/S64, no StageA, no StageB, no GRPO, no broad-LoRA, no checkpoint deletion, no video/image/checkpoint/local_assets push.

## Output Paths

- `reports/dpo_utility_calibration_v14/`
- `manifests/dpo_v14_subsets/`
- `docs/dpo_utility_calibration_v14_report.md`
- `configs/cam_physgeo/dpo_objective_v14_normalized.yaml`
- `configs/cam_physgeo/dpo_search_v14.yaml`
- `configs/cam_physgeo/dpo_v14_scheduler.yaml`
