Current Status:
BLOCKED

# Sigma Bin Check v8

The required full real-energy sigma-bin check was attempted on the same 10 reviewed GT>C pairs from `manifests/dpo_smoke_v7_gt_c_10.jsonl`.

## Attempt

- Command: `python -m cam_physgeo.dpo.objective_ablation sigma-bin-check ...`
- GPU: physical GPU4 via `CUDA_VISIBLE_DEVICES=4`
- Requested bins: low, mid, high
- Pair count: 10
- Precompute output: `reports/dpo_objective_diagnosis_v8/precompute_latents.csv`
- Log: `reports/dpo_objective_diagnosis_v8/sigma_bin_check.log`

## Result

Status: `SIGMA_ENERGY_CHECK_TIMEOUT`.

The job loaded the backend, completed latent precompute, loaded 16 model checkpoint shards, and entered the real energy forward loop. GPU4 stayed saturated, but no `sigma_bin_check.csv` with actual sigma/energy rows was produced within the 60 minute safety window. The tmux session was stopped intentionally.

No actual sigma values are reported here because the full energy check did not complete.

## Decision

Objective diagnosis v8 is blocked before training. Do not run winner-anchor-only, strict SDPO, linear-DPO, or safe-linear objectives until sigma mapping can be verified with a bounded runtime/progress-writing check.
