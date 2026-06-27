# Current Unified Eval / DPO Status

Updated: 2026-06-28T00:20:04

## Current Protocol State

- DPO training: not running.
- New pair protocol: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Valid pairs: 66.
- Type A local corruption: 50.
- Type B medium-hard rollout: 16.
- Prior DPO probe remains failed for scale-up; this protocol is the data repair step.

## Decision

Pair protocol v1 is ready for review and selected-subset real-energy audit. It is not approval to launch DPO automatically.

---

# Current Unified Eval / DPO Status

Updated: 2026-06-27T07:14:17

## Current Status

- Prefix-aware V2V-5 pairs: READY (`manifests/anchored_dpo_probe_pairs_prefix5.jsonl`, 50/50 visual-audited valid prefix5 pairs).
- Real LingBot-Fast prefix5 DPO energy backend: READY for preflight.
- DPO BF16 runtime: **DPO_BF16_READY**.
- Tiny DPO probe: **BLOCKED** until a verified V2V-5 LingBot-Fast generation wrapper is implemented for checkpoint video evaluation.
- No large-scale DPO, StageB, GRPO, or full-data long StageA was run in this step.

## Latest BF16 Preflight Outputs

- Matrix: `reports/dpo_bf16_preflight/matrix.csv`
- Energy summary: `reports/dpo_bf16_preflight/energy_checks_summary.csv`
- Single: `reports/dpo_bf16_preflight/lingbot_fast_single_gpu7_20260627_053617/`
- DDP2: `reports/dpo_bf16_preflight/lingbot_fast_ddp2_gpu67_20260627_060736/`
- DDP8: `reports/dpo_bf16_preflight/lingbot_fast_ddp8_gpu01234567_20260627_063825/`

## Why Probe Is Not Started Yet

The DPO trainer can now compute real energy and update LoRA. However the probe specification requires real V2V-5 rollout videos for every checkpoint. The current inference wrapper is image-first and would be I2V, not V2V-5. Running it would invalidate the probe.

