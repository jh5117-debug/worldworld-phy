# Physion Experiment Plan

Stage 0: HDF5/camera audit and reward calibration. No training.

Stage 1: Physion support warm-up. Short LoRA/adapter-only SFT-style warm-up with TRD auxiliary and replay. This is not the final method.

Stage 2: VideoGPA-based anchored DPO. Main method, but not launched until reward calibration passes. Start with clean Physion GT over corrupted GT pairs. LingBot-Base is a baseline only, not the default teacher, because it can also be weak in this domain.

Stage 3: self-rollout DPO. Only after pass@K, quality, background/camera reward, and freeze filters pass.

Benchmarks:

- Physion Camera-only Static
- Physion Static-camera Physics
- Physion Moving-camera Physics
- Physion Reobserve Split
- Physion OOD Templates

Baselines:

- LingBot-Fast zero-shot
- LingBot-Base zero-shot baseline
- old SFT checkpoint if available
- Stage1 Physion warm-up
- TRD-only
- GeoFlow-style reward only
- VideoGPA anchored DPO
- VideoGPA anchored DPO + TRD/camera adapter
- Self-rollout DPO after bootstrap
