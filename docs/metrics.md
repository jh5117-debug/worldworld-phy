# Physion Metrics

Primary:

- BRC: Background Rigid Consistency
- CAF: Camera Adherence / Following
- FG-ID: Foreground Identity
- ODS: Object Deformation Score
- PES: Physics Event Score
- RCS: Reobserve Consistency
- Freeze Rate
- Quality / Flicker / Blur

Reward calibration reports also include:

- `R_total`
- `R_total` without quality, so visual quality does not hide geometry failures
- `R_total` without physics, to diagnose whether the physical-event proxy is dominating
- per-corruption win rate for background drift, object deformation, color/identity change, reobserve mismatch, freeze foreground, and global freeze

DINOv2 is the preferred foreground/reobserve feature backend. V-JEPA2 or VideoMAE2 is the preferred temporal/TRD backend. If these checkpoints are absent, smoke tests use deterministic proxy visual features and mark the fallback explicitly.

Auxiliary:

- PSNR
- SSIM
- LPIPS
- PMF if legacy tooling is available

Auxiliary pixel metrics are not the main conclusion because they do not directly measure camera-conditioned physical world consistency.
