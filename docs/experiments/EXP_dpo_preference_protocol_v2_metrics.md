# EXP_dpo_preference_protocol_v2_metrics

Current Status: PASS_PARTIAL: metric wrappers added; PSNR/SSIM/LPIPS pass; FVD/VBench blocked by environment.
Updated: 2026-06-29 14:18:28

## Result Update

PASS_PARTIAL: metric wrappers added; PSNR/SSIM/LPIPS pass; FVD/VBench blocked by environment.

# EXP DPO Preference Protocol v2 Metrics

Current Status: PLANNED
Updated: 2026-06-29 11:49:16
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Experiment Goal

Make the metric stack auditable for protocol v2 and all later DPO run-throughs.

## Hypothesis

PSNR/SSIM can be made mandatory immediately, while LPIPS/FVD/VBench may be environment-blocked but must be surfaced explicitly rather than silently omitted.

## Input Data

Existing V2V-5 rollout videos, GT futures, protocol v1 pair manifests, and selected loser audits.

## Exact Model / Checkpoint

No training model is changed. Metrics are evaluated on existing Original Fast, StageA V2V-5, DPO step20, Type A, and Type B artifacts.

## Condition Format

All experiments use true V2V-5 prefix conditioning: prefix frames 0-4, prompt, poses, and intrinsics. Prediction, reward, and loss targets are future frames 5-80. `use_action=false` remains required.

## Pair Type

Applies to Type A local corruption and Type B GT-vs-rollout pairs.

## Metrics

Required metrics: PSNR, SSIM, LPIPS, FVD, VBench Total/Motion/Temporal/Quality when backends are available, plus PhysGeo BRC, CAF, FG-ID, ODS, PES, RCS, Freeze, Quality, Sharpness, and Blur. Missing LPIPS/FVD/VBench must be reported as `BLOCKED_BY_ENV` with attempted fix.

## Visual Audit Rule

Codex must inspect real videos or contact sheets. A candidate or checkpoint cannot pass on scalar metrics alone. Winner quality, loser collapse, blur, foreground identity, camera following, background stability, physical event, and reobserve behavior must be recorded.

## Success Gate

PSNR and SSIM wrappers pass smoke tests and produce per-sample outputs. LPIPS/FVD/VBench wrappers either run or produce structured blocked rows with reason and attempted fix.

## Failure / Blocked Gate

Blocked if PSNR/SSIM cannot be computed on local videos. LPIPS/FVD/VBench alone do not block protocol v2 if documented as environment-blocked.

## Output Paths

`reports/metrics_backend_readiness/metrics_backend_matrix.csv`, `reports/metrics_backend_readiness/metrics_backend_report.md`, `docs/metrics.md`.

## Explicitly Not Run

No StageB, no GRPO, no full-data long StageA, no large-scale DPO, no checkpoint deletion, and no data/weights/videos pushed to Git.

## Git Workflow

Pre-experiment checkpoint: commit and push this PRD before running the experiment. Post-experiment: update status, metrics, visual audit result, decision, blockers, and next action, then commit and push lightweight source/docs/CSV/JSON summaries only.
