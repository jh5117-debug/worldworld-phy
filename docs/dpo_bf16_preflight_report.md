# DPO BF16 Preflight Report (2026-06-27 04:43:25)

Current state before real preflight:
- Prefix5 training readiness: READY, 50/50 pairs.
- New backend: `cam_physgeo.dpo.lingbot_fast_energy.LingBotFastDpoEnergy`.
- CLI: `python -m cam_physgeo.training.train_stage2_anchored_dpo --backend lingbot_fast --run_preflight`.
- Unit tests for strict future mask, same noise/timestep, and frozen reference pass.

Preflight matrix is not complete yet. The next execution will attempt:
1. GPU7 single-process, 2 optimizer steps, 5 prefix5 pairs.
2. GPU6,7 DDP2 if single-process passes.
3. GPU0-7 DDP8 if DDP2 passes.

DPO status remains BLOCKED until real LingBot-Fast BF16 preflight passes.


---

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
