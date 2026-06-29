# Candidate Generator Small-LoRA v2 Report

Current Status: TRIGGERED_NOT_RUN
Updated: 2026-06-29 14:18:28

Protocol v2 found that Type B rollout losers were not usable after the stricter blur/sharpness gate. This triggers the candidate-generator line conceptually, but this turn did not start new StageA/candidate-generator training because the requested priority was to stabilize protocol v2 and run one small DPO engineering run-through.

## Trigger

- Type B candidates evaluated from protocol v1: 16
- Type B selected by v2: 0
- Rejected by blur/sharpness gate: 16
- Rejected by per-condition R_quality p40 gate: 10

## Decision

Do not use current rollout losers for DPO. Use Type A local-corruption pairs for engineering run-throughs. Candidate-generator v2 remains the next experiment if we need rollout-based medium-hard losers: camera-only rank8 and limited temporal/self-attention LoRA should be tested, with no broad LoRA and no FFN.
