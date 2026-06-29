# DPO preference protocol v3

Current Status: MIXED_TYPEA_READY_TYPEB_BLOCKED
Updated: 2026-06-29 15:16:36

## Experiment Goal

DPO preference protocol v3.

## Hypothesis

Build a stricter V2V-5 preference manifest with Type A local corruption and only sharpness-qualified Type B rollout losers.

## Exact Input Data

- V2V-5 prefix condition: frames 0-4.
- Prediction/evaluation target: future frames 5-80.
- Existing Protocol v2 manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`.
- Type A source: `reports/dpo_preference_protocol_v2/localdpo_ready_pairs_v2.jsonl`.
- Type B source candidates: v1/v2 rollout scoring and future candidate-generator outputs.

## Model / Checkpoint

- Base model: LingBot-World-Fast.
- Candidate generator candidates: Original Fast, old tiny camera LoRA if available, camera-only rank8, limited temporal/self-attention rank4.
- DPO smoke policy: only after v3 gates pass; no large DPO.

## LoRA Scope

- No broad-LoRA.
- No FFN.
- No all-block self/cross attention.
- Candidate generator may use camera-only rank8 or limited temporal/self-attention rank4 max 4 blocks.
- DPO smoke defaults to camera-conditioning rank4 unless diagnostics require limited temporal/self-attention.

## Condition Format

- `prefix_len = 5`.
- `prediction_start_frame = 5`.
- `use_action = false`.
- Prompt, poses, and intrinsics must match between winner and loser.

## Metrics

- PSNR / SSIM / LPIPS required where possible.
- FVD / VBench PASS or explicit `BLOCKED_BY_ENV` with attempted fix and next action.
- PhysGeo: BRC, CAF, FG-ID, ODS, PES, RCS, Freeze, Quality, Sharpness/Blur.

## Codex Visual Audit Rule

Every generated checkpoint/rollout used for a decision must have real V2V-5 video, contact sheet, and structured Codex audit. Metric gains without visual confirmation are not a PASS.

## Success / Fail / Blocked Gate

- PASS only if outputs are generated, metrics are computed or honestly blocked, and visual audit supports the decision.
- MIXED if Type A is usable but Type B remains blocked.
- BLOCKED if required inputs/backends are missing or GPUs remain unavailable for candidate-generator training.
- FAILED if videos degrade, are blurry, or preference pairs become too easy/collapsed.

## Output Paths

- Primary output root: `reports/dpo_preference_protocol_v3/`.
- Docs/report updates must be written after execution.

## Explicitly Not Run

- No StageB.
- No GRPO.
- No full-data long StageA.
- No large-scale DPO.
- No checkpoint/data deletion.
- No large artifact Git push.

## Git Commit Before / After

- Before experiment: `Prepare protocol v3 metrics candidate generator and DPO smoke PRDs`.
- After experiment: update this PRD with actual status, outputs, metrics, and decision, then commit/push lightweight artifacts.
