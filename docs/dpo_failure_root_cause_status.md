# DPO Failure Root-Cause Status

Updated: 2026-06-29 05:40 CST

## Current State

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Starting commit for this diagnosis: `8553d40`
- Preference protocol v1 is complete: 66 valid V2V-5 pairs.
- Full real LingBot-Fast energy audit is complete: 66/66 OK.
- DPO-ready pairs: 50 total, with 34 Type A local-corruption and 16 Type B medium-hard rollout losers.
- S0 objective ablation completed and failed signal gate. S1/S2 were not launched.

## Completed Diagnostics

- Diagnostic subsets: `manifests/dpo_diagnostics/`.
- Winner-only energy minimization: `reports/dpo_failure_diagnostics/winner_only_overfit.csv`.
- Loser-only energy maximization: `reports/dpo_failure_diagnostics/loser_only_overfit.csv`.
- Gradient decomposition: `reports/dpo_failure_diagnostics/gradient_decomposition.csv`.
- Timestep/sigma sensitivity: `reports/dpo_failure_diagnostics/timestep_sigma_sensitivity.csv`.
- Beta / utility scale analysis: `reports/dpo_failure_diagnostics/beta_utility_scale.csv`.
- LoRA scope capacity smoke: `reports/dpo_failure_diagnostics/lora_scope_capacity.csv`.
- LocalDPO mask audit: `reports/dpo_failure_diagnostics/localdpo_mask_audit.csv`.
- Consolidated summary: `reports/dpo_failure_diagnostics/diagnostic_summary.json`.
- Root-cause report: `docs/dpo_failure_root_cause_report.md`.

## Decision

Do not proceed with standard DPO or scale DPO. The next probe should add an explicit winner-anchor term, cap loser updates until winner energy improves, fix low/mid sigma sampling exposure, and connect spatial LocalDPO masks before claiming region-aware DPO.

## Safety

No large DPO, StageB, GRPO, full-data StageA, checkpoint deletion, data deletion, or data/weight/video push was performed.
