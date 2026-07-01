Current Status:
BLOCKED_WINNER_ANCHOR_1PAIR_OOM

# DPO Objective Diagnosis v8b Start Status

Updated: 2026-07-02 03:45 CST

## Why v8 Was Blocked

The v8 real-energy sigma/timestep precheck attempted the full 10 reviewed GT>C pairs across low/mid/high bins. Latent precompute completed and LingBot-Fast model shards loaded, but the energy loop saturated physical GPU4 and did not finish within the 60 minute safety window. Because the CSV was written only after the full loop, no actual sigma rows were produced.

Current v8 decision: `OBJECTIVE_BLOCKED_SIGMA_ENERGY_CHECK_TIMEOUT`. Winner-anchor-only, strict SDPO, Linear-DPO, and safe-linear objectives were not run.

## v8b Safety Change

v8b avoids long no-output periods by splitting the diagnosis into bounded stages:

1. Sampler-only sigma mapping check, no DiT, no VAE, no video reads, expected under one minute.
2. Real-energy smoke on one reviewed pair only, low/mid/high bins, append one CSV/JSONL row immediately after every bin.
3. Winner-anchor-only 1-pair 5-step sanity only if real-energy smoke passes.
4. 10-pair 20-step winner-anchor-only only if the 1-pair run improves winner energy.

## Scope

This round does not scale DPO. It does not run strict SDPO, Linear-DPO, safe-linear DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or pair-factory rollout.

## Pair Subset

Input subset: `manifests/dpo_smoke_v7_gt_c_10.jsonl`. The subset comes from previously reviewed GT>C medium-hard pairs with `codex_visual_audit.reviewed = true`; v8b does not create new DPO-ready pairs.

## Expected Outputs

- PRD: `docs/experiments/EXP_bounded_sigma_and_winner_anchor_v8b.md`
- Sampler-only sigma: `reports/dpo_objective_diagnosis_v8b/sigma_sampler_only.csv`
- One-pair real-energy smoke: `reports/dpo_objective_diagnosis_v8b/sigma_real_energy_smoke.csv`
- Winner-anchor 1-pair: `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_1pair_5step.csv`
- Final decision: `reports/dpo_objective_diagnosis_v8b/decision.json`

## Result Summary

- Sampler-only sigma: PASS.
- Real-energy sigma smoke: PASS on one reviewed pair, low/mid/high actual sigmas separated.
- Winner-anchor-only 1-pair: BLOCKED by CUDA OOM after one completed step; winner_improvement remained 0.0.
- 10-pair winner-anchor and SDPO/Linear variants were not run.
