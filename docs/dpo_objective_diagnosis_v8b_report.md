Current Status:
BLOCKED_WINNER_ANCHOR_1PAIR_OOM

# DPO Objective Diagnosis v8b Report

## Summary

v8b resolved the first v8 blocker: sigma/timestep mapping can be checked in a bounded way, and both sampler-only and 1-pair real-energy smoke showed separated low/mid/high actual sigma values. The next blocker is winner-anchor-only runtime/signal: the 1-pair 5-step run completed only one step and then hit CUDA OOM. The completed row had winner_improvement = 0.0, so the winner-preserving gate did not pass.

## Inputs

- Pair subset: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Pair used for real-energy and winner-anchor smoke: `v6b_GT_C_001_01014_drop_orbit_left_72_seed40014`
- GPU: physical GPU4 via `CUDA_VISIBLE_DEVICES=4`
- Objective for winner smoke: `winner_anchor_only`, `loss = E_policy_winner`, `lambda_loser = 0`

## Sampler-Only Sigma

- Status: `SIGMA_SAMPLER_ONLY_PASS`
- Output: `reports/dpo_objective_diagnosis_v8b/sigma_sampler_only.csv`
- low mean sigma: 0.125125
- mid mean sigma: 0.399900
- high mean sigma: 0.824925

This is schedule-only and does not replace real energy.

## Real-Energy Sigma Smoke

- Status: `SIGMA_REAL_ENERGY_SMOKE_PASS`
- Output: `reports/dpo_objective_diagnosis_v8b/sigma_real_energy_smoke.csv`
- actual low sigma: 0.1243339181
- actual mid sigma: 0.3495545387
- actual high sigma: 0.8247423172
- rows were appended incrementally by per-bin bounded commands

## Winner-Anchor-Only 1-Pair

- Status: `WINNER_ANCHOR_1PAIR_FAIL_OOM`
- Requested steps: 5
- Completed steps: 1
- Nonzero grad: true
- Final winner improvement: 0.0
- Final objective loss: 0.1511940509
- Runtime status: FAILED
- Error: CUDA OOM after one completed step; process-local cuda:0 corresponds to physical GPU4 under `CUDA_VISIBLE_DEVICES=4`

Output:

- `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_1pair_5step.csv`
- `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_1pair_summary.md`

## Not Run

- Winner-anchor-only 10-pair / 20-step: NOT_RUN_AFTER_1PAIR_FAIL
- Strict SDPO: blocked until winner-anchor-only passes
- Linear-DPO: blocked until winner-anchor-only passes
- Safe-linear DPO: blocked until winner-anchor-only passes
- Pair factory rollout: not run

## Decision

`V8B_BLOCKED_WINNER_ANCHOR_1PAIR_OOM`

DPO cannot proceed. The next fix should reduce winner-anchor memory pressure and/or add checkpointing/offload for the real training graph, then rerun the 1-pair winner-anchor-only gate before any SDPO or Linear-DPO variant.

## Pair Factory Bookkeeping

- Status: `NOT_RUN_V8B_OBJECTIVE_FIRST`
- Output: `reports/scale_gt_c_pair_factory_v8/condition_recovery_bookkeeping.csv`
- No new conditions, rollouts, or pairs were created.

## Tests

- `python -m compileall cam_physgeo src tests`: PASS
- `pytest -q tests/test_sigma_timestep_debug.py tests/test_dpo_same_noise_timestep.py tests/test_reference_frozen.py`: PASS, 6 passed

## Explicit Non-Runs

No large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, and no videos/weights pushed.
