# DPO Failure Root-Cause Status

Updated: 2026-06-29 03:05 CST

## Current State

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Starting commit for this diagnosis: `8553d40`
- Preference protocol v1 is complete: 66 valid V2V-5 pairs.
- Full real LingBot-Fast energy audit is complete: 66/66 OK.
- DPO-ready pairs: 50 total, with 34 Type A local-corruption and 16 Type B medium-hard rollout losers.
- S0 objective ablation completed and failed signal gate. S1/S2 will not be launched in this diagnosis.

## This Turn

This turn only diagnoses the failure root cause. It does not run large DPO, StageB, GRPO, or full-data StageA.

## Diagnostic Subsets

- D0: strongest Type B one-pair subset.
- D1: five strongest Type B pairs.
- D2: five strongest Type A pairs.
- D3: 4 Type B + 4 Type A, matching S0 style.

Subset files are under `manifests/dpo_diagnostics/` and summary is `reports/dpo_failure_diagnostics/subset_summary.csv`.

## Pending Diagnostics

- Winner-only energy minimization.
- Loser-only energy maximization.
- Winner/loser gradient decomposition.
- Timestep / sigma sensitivity.
- Beta / utility scale analysis.
- LoRA scope capacity smoke.
- LocalDPO mask audit.
