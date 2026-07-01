Current Status:
BLOCKED_WINNER_ANCHOR_1PAIR_OOM

# EXP Bounded Sigma and Winner-Anchor Diagnosis v8b

## Actual Result 2026-07-02

- PRD was committed and pushed before execution.
- Sampler-only sigma mapping completed and separated low/mid/high bins.
- One-pair real-energy smoke completed for low/mid/high with actual sigmas 0.1243339181, 0.3495545387, and 0.8247423172.
- Winner-anchor-only 1-pair run was attempted for 5 steps on physical GPU4.
- Completed steps: 1 / 5.
- Status: `WINNER_ANCHOR_1PAIR_FAIL_OOM`.
- Final winner improvement from completed row: 0.0.
- Nonzero grad: true.
- Save/load OK: false, because run failed before final save/load check.
- Error: CUDA OOM during the 1-pair winner-anchor-only run after one completed step. The error message names CUDA device 0 because `CUDA_VISIBLE_DEVICES=4` remaps physical GPU4 to process-local cuda:0.
- 10-pair winner-anchor, strict SDPO, Linear-DPO, and safe-linear DPO were not run.
- Decision: `V8B_BLOCKED_WINNER_ANCHOR_1PAIR_OOM`; DPO cannot proceed.


Updated: 2026-07-02 03:45 CST

This experiment follows `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`. It uses an already reviewed pair subset and does not create new DPO-ready pairs.

## Current Status

Tiny SDPO-anchor smoke v7 ran 20/20 steps with runtime PASS but objective signal fail: final winner improvement was negative, loser degradation was positive, and final winner contribution ratio was 0.0. v8 tried a full 10-pair real-energy sigma precheck, but the check timed out after saturating GPU4 and produced no actual sigma values.

## Problem

The v8 real-energy sigma check was too heavy and wrote results only after the whole job, so a 60 minute timeout left no usable actual sigma rows. Without verified low/mid/high sigma mapping, winner-anchor-only and DPO variants must not run.

## Hypothesis

A bounded staged diagnosis can isolate the blocker:

1. First verify sigma mapping with a sampler-only check that does not load LingBot-Fast.
2. Then run a 1-pair real-energy smoke that appends each bin result immediately.
3. Only if sigma mapping and 1-pair real-energy smoke pass, run a minimal winner-anchor-only optimization where `loss = E_policy_winner` and `lambda_loser = 0`.

If winner-anchor-only cannot reduce winner energy on one reviewed pair, then strict SDPO and Linear-DPO should remain blocked.

## Inputs

- Pair subset: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Reviewed source: v7/v6b GT>C medium-hard pairs
- Required condition: `codex_visual_audit.reviewed = true` for the pair subset
- Config: `configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml` unless the existing energy runner requires an equivalent v7 config

## GPU Policy

Use physical GPU4-7 only. If GPU4-7 are occupied, wait or select an idle GPU in that range. Do not use GPU0-3.

## Metrics

Sampler-only sigma mapping:

- requested_bin
- sample_idx
- timestep
- actual_sigma
- scheduler_name
- sigma_min
- sigma_max
- bin_low
- bin_high
- status

Real-energy smoke:

- pair_id
- requested_bin
- timestep
- actual_sigma
- E_ref_winner
- E_ref_loser
- E_policy_winner
- E_policy_loser
- Delta_ref
- Delta_policy
- reference_relative_margin
- seconds
- gpu
- status
- error_reason

Winner-anchor-only:

- step
- E_policy_winner
- E_ref_winner
- winner_improvement
- loss
- grad_norm
- update_norm
- LoRA param norm
- lr
- timestep
- actual_sigma
- gpu memory
- step_time
- finite
- status

## Success Gate

- Sampler-only low/mid/high actual sigma distributions are separated.
- 1-pair real-energy smoke writes all three bin rows incrementally and completes.
- Winner-anchor-only 1-pair 5-step run completes with finite values.
- Winner-anchor-only is signal-positive only if final and mean winner improvement are both greater than zero.

## Failure Gate

- `SIGMA_MAPPING_BROKEN`: low/mid/high bins collapse to the same actual sigma.
- `SIGMA_MAPPING_PASS_ENERGY_TOO_SLOW`: sampler mapping passes but one-pair real-energy rows are too slow or timeout.
- `WINNER_ANCHOR_1PAIR_FAIL`: winner-anchor-only completes but winner improvement is not positive.
- Any OOM, SIGFPE, NaN/Inf, wrong GPU, or missing reviewed pair subset blocks further objective runs.

## Output Paths

- root: `reports/dpo_objective_diagnosis_v8b/`
- sampler CSV: `reports/dpo_objective_diagnosis_v8b/sigma_sampler_only.csv`
- sampler summary: `reports/dpo_objective_diagnosis_v8b/sigma_sampler_only_summary.md`
- real-energy smoke CSV: `reports/dpo_objective_diagnosis_v8b/sigma_real_energy_smoke.csv`
- real-energy smoke JSONL: `reports/dpo_objective_diagnosis_v8b/sigma_real_energy_smoke.jsonl`
- real-energy smoke summary: `reports/dpo_objective_diagnosis_v8b/sigma_real_energy_smoke_summary.md`
- winner 1-pair CSV: `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_1pair_5step.csv`
- winner 1-pair summary: `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_1pair_summary.md`
- winner 10-pair CSV: `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_10pair_20step.csv`
- winner 10-pair summary: `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_10pair_summary.md`
- decision: `reports/dpo_objective_diagnosis_v8b/decision.json`
- report: `docs/dpo_objective_diagnosis_v8b_report.md`

## What Is Not Run

No large DPO, no strict SDPO, no Linear-DPO, no safe-linear DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no pair-factory rollout, no checkpoint deletion, no checkpoint overwrite, no video/weight push, and no unreviewed loser manifest.

## Git Checkpoint

- Before execution commit: `Prepare bounded sigma and winner-anchor diagnosis v8b PRD`
- After sampler implementation commit: `Add bounded sigma timestep diagnostics`
- After execution commit: `Run bounded winner-anchor diagnosis v8b`
