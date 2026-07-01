Current Status:
BLOCKED

# DPO Objective Diagnosis v8 Report

## Summary

Winner-preserving objective diagnosis v8 did not reach objective training. The required sigma/timestep precheck was attempted with the true LingBot-Fast DPO energy backend on the same 10 reviewed GT>C pairs from v7, but the full 10-pair low/mid/high real-energy check exceeded the 60 minute safety window without producing actual sigma rows.

## Sigma Bin Check

- Pair manifest: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Pair count: 10
- Requested bins: low, mid, high
- GPU: physical GPU4
- Precompute: completed; see `reports/dpo_objective_diagnosis_v8/precompute_latents.csv`
- Backend load: completed; 16 checkpoint shards loaded
- Energy loop: entered and saturated GPU4
- Output status: `SIGMA_ENERGY_CHECK_TIMEOUT`
- Actual sigma values: not reported, because the full check did not complete

## Objective Results

- Winner-anchor-only: NOT_RUN
- Strict SDPO-anchor: NOT_RUN
- Linear-DPO + winner-anchor: NOT_RUN
- Safe-linear DPO: NOT_RUN

Reason: objective training is blocked until sigma mapping is verified.

## Decision

`OBJECTIVE_BLOCKED_SIGMA_ENERGY_CHECK_TIMEOUT`

Do not proceed to winner-anchor-only or any DPO objective variant until the sigma-bin check is made bounded and progress-writing. The next implementation should write per-pair/per-bin rows incrementally and/or first run a schedule-only sigma mapping check, clearly labeled as not a replacement for real energy evaluation.

## Not Run

No large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, no unreviewed loser manifest, and no data/weights/video push.
