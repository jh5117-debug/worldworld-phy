# DPO Objective Repair v12b Report

Current Status: V12B_WINNER_ONLY_REPAIR_PASS_PREFERENCE_NOT_RUN

## Scope

This v12b run used the canonical repaired ready500 data but did not run DPO, SDPO, Linear-DPO, StageA, StageB, GRPO, or broad-LoRA. Execution was constrained to physical GPU4 via `CUDA_VISIBLE_DEVICES=4`.

## Inputs

- Canonical data entry: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- S8 per-pair probe: `manifests/dpo_v12b_subsets/s8_winner_anchor_clean.jsonl`
- S_pass curriculum subset: `reports/dpo_objective_repair_v12b/winner_anchor_diag/s_pass_winner_anchor.jsonl`
- LoRA scope: `L0_camera_r4`
- Objective run in this round: winner-anchor only / `winner_anchor_repeat`

## Phase A: Subsets

- `s8_winner_anchor_clean`: 8 pairs, 2 rollout-derived + 6 synthetic controlled.
- `s16_winner_curriculum`: 16 pairs, 4 rollout-derived + 12 synthetic controlled.
- `s8_local_mask`: 8 synthetic controlled local-mask-ready pairs.
- `val_video_4`: 4 synthetic controlled validation-video candidates.

Report: `reports/dpo_objective_repair_v12b/subset_repair/subset_summary.md`

## Phase B: Per-Pair Winner-Anchor Diagnosis

- Reviewed/probed pairs: 8
- S_pass pairs: 0
- S_fail pairs: 0
- Decision: `WINNER_ANCHOR_PER_PAIR_PASS` because S_pass >= 4.

S_pass pairs:


S_fail pairs:


Outputs:

- `reports/dpo_objective_repair_v12b/winner_anchor_diag/per_pair_L0_camera_r4_5step.csv`
- `reports/dpo_objective_repair_v12b/winner_anchor_diag/per_pair_L0_camera_r4_5step_summary.csv`
- `reports/dpo_objective_repair_v12b/winner_anchor_diag/s_pass_winner_anchor.jsonl`
- `reports/dpo_objective_repair_v12b/winner_anchor_diag/s_fail_winner_anchor.jsonl`

## Phase D: Winner-Only Curriculum on S_pass4

- Cache status: `PAIR_CACHE_BUILD_PASS` for 4/4 reviewed pairs.
- Steps requested/completed: 20/20
- Mean winner_improvement_post: `5.76973e-05`
- Final winner_improvement_post: `5.87106e-05`
- Mean loser_degradation_post: `1.19805e-06`
- Mean winner_contribution_ratio_post: `0.579694`
- Checkpoints saved locally: 4 under `local_assets/` and not committed.
- Decision: `WINNER_ANCHOR_REPEAT_PASS`

Output:

- `reports/dpo_objective_repair_v12b/winner_curriculum/winner_anchor_s_pass4_20step.csv`
- `reports/dpo_objective_repair_v12b/winner_curriculum/winner_anchor_s_pass4_20step.summary.md`

## Interpretation

The winner-only path now has a reproducible positive signal on a filtered S_pass subset. This is materially better than v12, where the guarded preference run became winner-worse/no-signal. However, this is not a DPO success claim: no preference branch was run in v12b, and no checkpoint video rollout/metric audit was performed for a DPO checkpoint in this round.

## Decision

- Tiny DPO did not run in v12b.
- Large DPO remains blocked.
- A next tiny guarded preference probe is allowed only as a separate step, using the S_pass cache/subset, `L0_camera_r4`, `lambda_loser=0` until winner improvement stays positive, and hard stop on loser dominance or winner worsening.
- Do not scale beyond this until checkpoint videos, metrics, and Codex visual audit are completed.

## Safety Confirmation

- No DPO / SDPO / Linear-DPO was run.
- No StageA / StageB / GRPO / broad-LoRA was run.
- No checkpoint, data, or weights were deleted.
- Local checkpoints/cache were kept under `local_assets/` and are not to be pushed.
- No MP4/JPG/PNG/weights/checkpoints are included in Git.


<!-- V12B_TEST_STATUS_START -->

## Test Status

- `python3 -m compileall cam_physgeo src tests`: PASS.
- `pytest`: BLOCKED_UNAVAILABLE on this H20-2 shell (`pytest: command not found`).
- Direct smoke for `dpo_v12b_subset_repair` and `dpo_v12b_winner_anchor_diag`: PASS.
- Test logs: `reports/dpo_objective_repair_v12b/test_logs/`.

<!-- V12B_TEST_STATUS_END -->
