# DPO BF16 Preflight Report

Updated: 2026-06-27 01:28:06

## Diagnostic Energy Backend

- Status: `PASS`
- Backend: `diagnostic_energy`
- Pairs used: `5`
- Steps: `2`
- Same noise: `True`
- Same timestep: `True`
- Save/load OK: `True`
- Final DPO loss: `0.6926472783088684`
- Final grad norm: `0.04997500032186508`
- Metrics: `reports/dpo_bf16_preflight/diagnostic_energy/training_metrics.jsonl`

This confirms pair plumbing and DPO loss direction only.

## LingBot-Fast Backend

- Status: `BLOCKED_FAST_ENERGY_BACKEND`
- Reason: LingBot-Fast rollout initialization is available in prior artifacts, but the anchored DPO energy path has not yet exposed a callable winner/loser flow-matching energy function with frozen reference.

## BF16 Decision

DPO BF16 formal readiness is **BLOCKED** until the real LingBot-Fast winner/loser energy backend is callable. StageA BF16 readiness does not automatically transfer to DPO because DPO uses a different two-video policy/reference computation path.
