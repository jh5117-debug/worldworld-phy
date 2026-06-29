# EXP_candidate_generator_small_lora_v2

Current Status: TRIGGERED_NOT_RUN: TypeB blur gate triggered this line, but no new generator training was started in this run.
Updated: 2026-06-29 14:18:28

## Result Update

TRIGGERED_NOT_RUN: TypeB blur gate triggered this line, but no new generator training was started in this run.

# EXP Candidate Generator Small-LoRA v2

Current Status: PLANNED
Updated: 2026-06-29 11:49:16
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Experiment Goal

Only if Type B is insufficient, test whether small, conservative LoRA candidate generators can produce clearer rollout losers/candidates.

## Hypothesis

Camera-only or limited temporal/self-attention LoRA may yield clearer candidate rollouts than broad-LoRA without destroying foreground identity, but success must be judged by rollout usability rather than training loss.

## Input Data

V2V-5 pilot train/val/test manifests and screen conditions used in existing StageA V2V-5 evaluation.

## Exact Model / Checkpoint

LingBot-Fast; candidates are G0 Original Fast, G1 old tiny camera-LoRA if available, G2 camera-only rank8, G3 camera + limited temporal/self-attn rank4 max 4 blocks, G4 small mixed-noise detail refinement.

## Condition Format

All experiments use true V2V-5 prefix conditioning: prefix frames 0-4, prompt, poses, and intrinsics. Prediction, reward, and loss targets are future frames 5-80. `use_action=false` remains required.

## Pair Type

Candidate generator produces possible Type B rollout losers/candidates; it does not directly train DPO.

## Metrics

Required metrics: PSNR, SSIM, LPIPS, FVD, VBench Total/Motion/Temporal/Quality when backends are available, plus PhysGeo BRC, CAF, FG-ID, ODS, PES, RCS, Freeze, Quality, Sharpness, and Blur. Missing LPIPS/FVD/VBench must be reported as `BLOCKED_BY_ENV` with attempted fix.

## Visual Audit Rule

Codex must inspect real videos or contact sheets. A candidate or checkpoint cannot pass on scalar metrics alone. Winner quality, loser collapse, blur, foreground identity, camera following, background stability, physical event, and reobserve behavior must be recorded.

## Success Gate

Generated videos remain at least as sharp as Original Fast, visual quality and foreground identity do not degrade, pass@K for usable medium-hard rollout negatives improves, and Codex video audit supports use.

## Failure / Blocked Gate

If videos are blurrier or less stable than Original Fast, do not use the generator and fall back to Type A/local corruption plus any Type B that passes gate.

## Output Paths

`docs/candidate_generator_small_lora_v2_report.md`, `reports/candidate_generator_v2/`, `manifests/candidate_generator_v2_rollouts.jsonl` if run.

## Explicitly Not Run

No StageB, no GRPO, no full-data long StageA, no large-scale DPO, no checkpoint deletion, and no data/weights/videos pushed to Git.

## Git Workflow

Pre-experiment checkpoint: commit and push this PRD before running the experiment. Post-experiment: update status, metrics, visual audit result, decision, blockers, and next action, then commit and push lightweight source/docs/CSV/JSON summaries only.
