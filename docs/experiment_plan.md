# Physion Experiment Plan

Stage 0: HDF5/camera audit and reward calibration. No training.

Stage 1: Physion support warm-up. Short LoRA/adapter-only SFT-style warm-up with TRD auxiliary and replay. This is not the final method.

Stage 2: anchored DPO. Main method. Start with clean Physion GT over corrupted GT pairs, then add LingBot-Base teacher over Fast rollout and high-score over low-score Fast rollout when rollouts exist.

Stage 3: self-rollout DPO. Only after pass@K, quality, background/camera reward, and freeze filters pass.

Benchmarks:

- Physion Camera-only Static
- Physion Static-camera Physics
- Physion Moving-camera Physics
- Physion Reobserve Split
- Physion OOD Templates

Baselines:

- LingBot-Fast zero-shot
- LingBot-Base zero-shot
- old SFT checkpoint if available
- Stage1 Physion warm-up
- TRD-only
- GeoFlow-style reward only
- Anchored DPO
- Anchored DPO + TRD
- Self-rollout DPO after bootstrap
