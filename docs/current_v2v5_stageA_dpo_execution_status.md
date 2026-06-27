# Current V2V-5 StageA / DPO Execution Status

Updated: 2026-06-27

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Baseline commit before wrapper work: `53d8882`
- Prefix5 pairs: READY, `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`, 50/50 valid.
- DPO energy backend: READY, real LingBot-Fast energy.
- DPO BF16 preflight: READY for single GPU, DDP2 and DDP8.
- Current focus: replace image-first Fast inference with honest V2V-5 generation.

## Fixed Blocker

The old inference path called `pipe.generate(prompt, image, action_path=...)`, which encoded only frame 0. The new wrapper constructs a prefix-video condition: frames 0-4 are encoded, frames 5-80 are zeroed, and evaluation uses future frames only.

## Not Running

No StageB, no GRPO, no large-scale DPO, no full-data long StageA, no data/checkpoint deletion, and no generated videos/checkpoints are pushed to Git.
