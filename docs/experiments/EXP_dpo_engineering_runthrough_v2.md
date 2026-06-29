# EXP_dpo_engineering_runthrough_v2

Current Status: PASS_ENGINEERING_ONLY: 8 TypeA pairs, sdpo_anchor, 10 steps, checkpoint save/load/video/metrics complete; learning signal still loser-dominant.
Updated: 2026-06-29 14:18:28

## Result Update

PASS_ENGINEERING_ONLY: 8 TypeA pairs, sdpo_anchor, 10 steps, checkpoint save/load/video/metrics complete; learning signal still loser-dominant.

# EXP DPO Engineering Runthrough v2

Current Status: PLANNED
Updated: 2026-06-29 11:49:16
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Experiment Goal

After protocol v2 passes, run a tiny DPO engineering smoke to verify forward/backward/save/eval/video/metrics plumbing, not to claim model improvement.

## Hypothesis

An SDPO-style objective with explicit winner anchor and conservative loser lambda can run stably on 8 pairs and produce evaluable checkpoints even if preference signal remains inconclusive.

## Input Data

`manifests/dpo_preference_protocol_v2_pairs.jsonl`, selecting 8 pairs: 4 Type A plus 4 Type B if Type B passes gate; otherwise 8 Type A.

## Exact Model / Checkpoint

LingBot-Fast with camera-conditioning LoRA rank4, BF16 mixed-safe, frozen reference, prefix_len=5, future-only loss.

## Condition Format

All experiments use true V2V-5 prefix conditioning: prefix frames 0-4, prompt, poses, and intrinsics. Prediction, reward, and loss targets are future frames 5-80. `use_action=false` remains required.

## Pair Type

Small mixed or Type-A-only DPO run-through; no S1/S2 scaling.

## Metrics

Required metrics: PSNR, SSIM, LPIPS, FVD, VBench Total/Motion/Temporal/Quality when backends are available, plus PhysGeo BRC, CAF, FG-ID, ODS, PES, RCS, Freeze, Quality, Sharpness, and Blur. Missing LPIPS/FVD/VBench must be reported as `BLOCKED_BY_ENV` with attempted fix.

## Visual Audit Rule

Codex must inspect real videos or contact sheets. A candidate or checkpoint cannot pass on scalar metrics alone. Winner quality, loser collapse, blur, foreground identity, camera following, background stability, physical event, and reobserve behavior must be recorded.

## Success Gate

No SIGFPE/OOM/NaN, same noise/timestep verified, reference frozen, future-only loss true, checkpoint save/load true, videos generated, metrics computed, and Codex visual audit completed.

## Failure / Blocked Gate

Runtime instability, missing future-only mask, reference not frozen, metrics/eval cannot run, or visual collapse. Positive DPO learning is not required for an engineering PASS.

## Output Paths

`docs/dpo_engineering_runthrough_v2_report.md`, `reports/dpo_engineering_runthrough_v2/`.

## Explicitly Not Run

No StageB, no GRPO, no full-data long StageA, no large-scale DPO, no checkpoint deletion, and no data/weights/videos pushed to Git.

## Git Workflow

Pre-experiment checkpoint: commit and push this PRD before running the experiment. Post-experiment: update status, metrics, visual audit result, decision, blockers, and next action, then commit and push lightweight source/docs/CSV/JSON summaries only.
