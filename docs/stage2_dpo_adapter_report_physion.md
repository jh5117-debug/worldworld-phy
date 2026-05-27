# Stage2 DPO Adapter Report

Implemented:

- Anchored pair JSONL schema.
- Pair dataset filtering by margin, winner reward, and freeze penalty.
- Energy-form DPO loss helper for diffusion/flow models.
- `gt_vs_corrupt` pair builder that generates corrupted videos, scores clean and corrupt samples, and keeps pairs by measured reward margin.

Still TODO before real training:

- Connect LingBot policy/ref models to a same-noise, same-timestep denoising or velocity error adapter.
- Freeze reference model.
- Limit updates to LoRA/adapter.
- Add TRD and light-SFT regularizers in the real optimizer loop.

Dry-run is supported; real training intentionally raises until the adapter is connected.
