# Candidate Generator Small-LoRA v2 Report

Current Status: CANDIDATE_GENERATOR_FAILED_TYPEB_STILL_BLOCKED

Updated: 2026-06-30 03:14:25

## What was audited

Reused existing true V2V-5 overnight small-LoRA rollouts from `local_assets/overnight_quant_lora_dpo_20260624_overnight_test/` because they already contain Original Fast plus A/B/C/D small-LoRA checkpoints and screen16 rollouts/contact sheets.

Codex visually inspected overview sheets for `original_fast`, `A_step050`, `B_step050`, `C_step050`, and `D_step050`. D_step050 had previously been selected by proxy metrics, but the visual overview is still too similar to Original Fast and does not produce clearly sharper, quality-qualified TypeB losers.

## Decision

- Rollout candidates audited: 208
- TypeB usable count: 0
- Selected generator: fallback to TypeA-only; no TypeB rollout loser admitted.
- FVD: BLOCKED_BY_ENV; no true local video FVD/I3D backend.
- VBench: BLOCKED_BY_ENV; no local evaluator/weights.

No broad-LoRA, StageB, GRPO, full-data StageA, or large-scale DPO was run.
