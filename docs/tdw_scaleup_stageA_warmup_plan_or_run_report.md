# TDW Scaleup Stage A Warmup Plan Or Run Report

Status: planned, not run in this phase.

Reason:

- The v5 1000 dataset is structurally valid.
- However, the prompt blocker was discovered: the official 1000 manifest still points to one generic prompt for all samples.
- `combined_prompt_v2` manifest has now been generated and should be used for future prompt-conditioned rollout/warmup checks.
- Multi-display TDW setup is not ready, so GPU scheduling between TDW generation and LingBot warmup is unresolved.
- A 1000-step Stage A run may exceed the lightweight planning window and should be scheduled after display/resource allocation is decided.

Recommended next Stage A command should use:

- dataset: 1000 split;
- prompt manifest: combined_prompt_v2 where supported;
- timestep: high-noise diagnostic;
- sampler: balanced;
- trainable scope: camera adapter LoRA only;
- no full model checkpoint;
- no optimizer state;
- GPU4-7 only;
- no DPO.
