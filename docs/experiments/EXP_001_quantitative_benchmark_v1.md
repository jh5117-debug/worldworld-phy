# EXP_001 Quantitative Benchmark v1

Updated: 2026-06-24 12:47:51 CST  
Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`  
Branch: `research/quant-small-lora-dpo-probe-20260624`  
Start commit: `63d1b93`  

This PRD is written before experiment launch. It must be updated after results are parsed and before the next stage is considered complete.


## Problem and Hypothesis

Training loss and fixed-val flow loss do not predict rollout quality. A fixed, leakage-checked benchmark is required before selecting LoRA scopes or DPO candidates.

Hypothesis: Original Fast, last-week camera-only tiny LoRA, and current broad-LoRA variants differ in foreground identity, camera/background consistency, and physical event preservation in ways not captured by flow loss.

## Unique Variable

Evaluation only. No model weights are changed.

## Base Models

- M0 Original LingBot-Fast: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`
- M1 last-week camera-only tiny LoRA: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt`
- M2 broad-LoRA step800: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/formal_fast_stageA_high_only_balanced_snapshot_20260622_1830_20260622_1925/checkpoints/fast_stageA_high_only_balanced_snapshot_20260622_1830/high_only_phase/branches/step_000800/fast_stageA_high_noise_adapter`
- M3 broad-LoRA final883: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/formal_fast_stageA_high_only_balanced_snapshot_20260622_1830_20260622_1925/checkpoints/fast_stageA_high_only_balanced_snapshot_20260622_1830/high_only_phase/branches/final/fast_stageA_high_noise_adapter`

## Data Manifest and SHA256

To be built under `manifests/quant_benchmark_v1_*.jsonl` from held-out stage1-ready generated_v5 samples. Core: 64 conditions, stress: 16 conditions, total: 80.

## Prompt Version

Use the prompt embedded in the selected converted sample manifest. Record exact prompt text and hash per sample.

## Metrics

Primary: ADE, DTW trajectory distance, endpoint error, event timing error, Mask IoU, st-IoU, area/aspect drift, contour deformation, FG-ID, object persistence, disappearance/duplication rate, PES, RCS, freeze/blur/flicker/quality.

Auxiliary diagnostic: BRC, CAF, Epipolar Sampson error, C-SGC. Epipolar/C-SGC are not DPO-ready alone.

## Video Audit Standard

Every generated video must receive a Codex structured audit row with 0/1/2 ratings and failure tags. No PASS without all-video audit.

## Success Gate

Benchmark is PASS if manifests are leakage-free, all selected model rollouts are generated/readable, summary tables include mean/median/std/paired delta/win-rate/bootstrap CI, and every video has an audit row. Benchmark does not select a model by itself.

## Outputs

- `manifests/quant_benchmark_v1_all.jsonl`
- `reports/quant_benchmark_v1/`
- `reports/video_audit/quant_benchmark_v1/`
- `docs/quantitative_benchmark_v1_report.md`

## Stop Conditions

Stop benchmark if conditions leak train scenes, model inference fails for all variants, or video audit cannot be produced.

## Git Commit

Pre-launch PRD commit: `Add quantitative benchmark and small-LoRA sweep PRDs`.

## Status

MANIFEST_READY; ROLLOUT_PENDING_SMALL_LORA_CHECKPOINTS.


## 2026-06-24 Manifest Build Result

Status: MANIFEST_READY.

Generated benchmark manifests:

- `manifests/quant_benchmark_v1_all.jsonl` = 80 conditions
- `manifests/quant_benchmark_v1_core.jsonl` = 64 conditions
- `manifests/quant_benchmark_v1_stress.jsonl` = 16 conditions
- `manifests/quant_benchmark_v1_summary.json`

Core uses val/test-holdout only and excludes train sample_id and scene_group_id. Core is balanced at 16 conditions each for drop, collision, roll, and containment. Stress uses remaining non-train camera-heavy/OOD-style conditions; current reobserve source is empty, so stress is diagnostic and does not claim true reobserve coverage.

Overlap with sweep train:

- sample overlap: 0
- scene overlap: 0

Rollout and metric execution are pending small-LoRA sweep checkpoints.
