# EXP_dpo_objective_repair_v12b

## Current Status

- Canonical repaired ready500 exists at `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Repaired train/val/test/top50 splits exist; deprecated old ready500 must not be used.
- v12 LoRA scope sanity selected `L0_camera_r4` as the only passing diagnostic scope.
- v12 tiny guarded SDPO-anchor on S1 failed and was stopped at step10 because winner improvement turned negative, contribution ratio reached zero, and DPO loss stayed near 0.693.
- DPO cannot scale. Current task is objective repair only.
- v12b must use physical GPU4 only via `CUDA_VISIBLE_DEVICES=4`.

## Problem

- The DPO preference branch may activate before winner-side energy is stable.
- Winner improvement was not robust across the 32-pair v12 S1 subset.
- Pair mixture may create gradient conflict, especially because controlled synthetic pairs dominate ready500.
- Standard sigmoid-style preference loss can sit near 0.693 with little useful margin.
- Loser degradation can dominate if loser branch opens too early.
- LocalDPO spatial/time masks are available for some synthetic pairs but are not fully exploited.

## Hypothesis

- A smaller high-confidence subset can expose stable winner-anchor behavior.
- Per-pair winner-anchor diagnosis can identify conflicting pairs before any preference training.
- Winner-only curriculum should run before any preference branch.
- Loser branch must remain disabled until winner improves for at least five consecutive eval windows.
- If a preference branch is tested, it must use tiny lambda values: `max_lambda_loser <= 0.05` and `max_lambda_pref <= 0.05`.
- Linear utility should not run unless winner-only curriculum passes.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- v12 subsets and reports if available.

## GPU Policy

- Physical GPU4 only.
- Commands must use `CUDA_VISIBLE_DEVICES=4` and process-local `--gpu 0`.
- GPU0/1/2/3/5/6/7 are forbidden for this run.
- If GPU4 is unavailable, mark `V12B_GPU4_BLOCKED`; do not fall back to another GPU.

## Success Gate

- Winner-only 5/10/20-step diagnostics improve winner energy.
- Mean and final `winner_improvement_post` are positive.
- If loser branch is enabled, `winner_contribution_ratio >= 0.30` and loser degradation is not the sole source of margin.
- No OOM / NaN / SIGFPE.
- Checkpoint videos and metrics are not worse than step0.
- Codex visual audit does not show worse quality, freeze, hallucination, foreground identity loss, camera failure, or reobserve degradation.

## Failure Gate

- Winner-only remains negative.
- Most per-pair winner-anchor diagnostics are negative.
- Loser branch dominates.
- DPO loss remains stuck near 0.693.
- Videos or metrics degrade.
- GPU4 is unavailable or runtime OOM occurs on GPU4.

## Planned Outputs

- `manifests/dpo_v12b_subsets/*.jsonl`
- `reports/dpo_objective_repair_v12b/`
- `docs/dpo_objective_repair_v12b_report.md`
- `reports/dpo_objective_repair_v12b/self_review.md`

## What Is Not Run

- No large DPO.
- No full train400.
- No S2/S3 scale.
- No StageA / StageB / GRPO.
- No broad-LoRA.
- No GPU5/6/7 fallback.
- No checkpoint deletion.
- No video/image/checkpoint/weight push.


<!-- V12B_EXECUTION_RESULTS_START -->

## Execution Results

- Phase A subsets: ready.
- Phase B per-pair winner-anchor diagnosis: 4 S_pass / 4 S_fail, `WINNER_ANCHOR_PER_PAIR_PASS`.
- Phase D S_pass4 winner-only curriculum: 20/20 steps, `WINNER_ANCHOR_REPEAT_PASS`.
- Mean winner_improvement_post: `5.76973e-05`.
- Final winner_improvement_post: `5.87106e-05`.
- Mean winner contribution ratio: `0.579694`.
- Preference/DPO branch: not run in this round.
- Updated: 2026-07-05 05:54:06.

<!-- V12B_EXECUTION_RESULTS_END -->
