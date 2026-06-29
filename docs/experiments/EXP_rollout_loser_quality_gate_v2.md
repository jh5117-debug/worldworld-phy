# EXP Rollout Loser Quality Gate v2

Current Status: PLANNED
Updated: 2026-06-29 11:49:16
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Experiment Goal

Re-screen Type B rollout losers so medium-hard negatives are clear, readable, non-collapsed, and not selected merely because they are blurry.

## Hypothesis

Most protocol v1 Type B rollout losers will fail a sharpness-aware quality gate; Type B should be used only if it passes visual and sharpness thresholds.

## Input Data

`reports/dpo_preference_protocol_v1/rollout_scores.csv`, `rollout_video_audit.csv`, `selected_medium_hard_losers.csv`, `full_real_energy_audit.csv`, and `manifests/dpo_preference_protocol_v1_pairs.jsonl`.

## Exact Model / Checkpoint

No model training. Existing rollout candidates from Original Fast, StageA V2V-5 final, and DPO step20 are audited.

## Condition Format

All experiments use true V2V-5 prefix conditioning: prefix frames 0-4, prompt, poses, and intrinsics. Prediction, reward, and loss targets are future frames 5-80. `use_action=false` remains required.

## Pair Type

Type B: winner = clean GT future, loser = medium-hard rollout future.

## Metrics

Required metrics: PSNR, SSIM, LPIPS, FVD, VBench Total/Motion/Temporal/Quality when backends are available, plus PhysGeo BRC, CAF, FG-ID, ODS, PES, RCS, Freeze, Quality, Sharpness, and Blur. Missing LPIPS/FVD/VBench must be reported as `BLOCKED_BY_ENV` with attempted fix.

## Visual Audit Rule

Codex must inspect real videos or contact sheets. A candidate or checkpoint cannot pass on scalar metrics alone. Winner quality, loser collapse, blur, foreground identity, camera following, background stability, physical event, and reobserve behavior must be recorded.

## Success Gate

At least 10 Type B losers pass sharpness ratio >= 0.55, visual_quality >= 1, R_quality >= candidate p40, no collapsed/black/global-freeze/scene-replacement failure, positive reward and energy margins, and Codex visual validity.

## Failure / Blocked Gate

If fewer than 10 Type B losers pass, protocol v2 must rely mainly on Type A and mark Type B blocked by blur/quality gate.

## Output Paths

`reports/dpo_preference_protocol_v2/typeB_loser_quality_gate.csv`, selected/rejected CSVs, and `typeB_quality_gate_report.md`.

## Explicitly Not Run

No StageB, no GRPO, no full-data long StageA, no large-scale DPO, no checkpoint deletion, and no data/weights/videos pushed to Git.

## Git Workflow

Pre-experiment checkpoint: commit and push this PRD before running the experiment. Post-experiment: update status, metrics, visual audit result, decision, blockers, and next action, then commit and push lightweight source/docs/CSV/JSON summaries only.
