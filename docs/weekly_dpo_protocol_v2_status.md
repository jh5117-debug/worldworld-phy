# Weekly DPO Protocol v2 Status

Current Status: IN_PROGRESS
Updated: 2026-06-29 11:49:16
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Current Facts

- V2V-5 wrapper is connected: prefix frames 0-4 are condition, future frames 5-80 are prediction/evaluation target.
- Prefix5 pairs were rebuilt and real LingBot-Fast energy backend is runnable.
- DPO BF16 preflight previously passed on single GPU, DDP2, and DDP8.
- Preference protocol v1 produced 66 valid pairs: 50 Type A local corruption and 16 Type B GT-vs-rollout pairs.
- Full real-energy audit selected 50 DPO-ready pairs: 34 Type A and 16 Type B.
- S0 objective ablation failed: standard energy-DPO had weak signal; SDPO-style was closest but did not meet winner-preservation gate; Linear-DPO and LocalDPO-style were loser-dominant.
- Failure diagnostics show unstable winner-only improvement, gradient conflict, high-noise-only sigma behavior, and missing spatial-token LocalDPO masking.
- PPT blur audit shows Type B rollout losers are often visually blurry; the old quality floor was too loose.

## Why DPO Cannot Be Scaled Directly

The current training path is runtime-capable, but the preference signal is not yet reliable. DPO losses around the no-margin region and loser-dominant updates indicate that scaling would likely spend compute amplifying bad gradients rather than improving V2V-5 generation.

## Why Type B Needs Re-screening

Type B has stronger real-energy margin than Type A, but many selected rollout losers fail visual sharpness. A usable medium-hard loser must remain clear and plausible while showing a specific physical, camera, foreground, or reobserve failure. Blur cannot be the hidden reason that reward selects the loser.

## This Week's Target

This week focuses on preference protocol v2 plus metrics readiness and one small engineering run-through:

1. Make PSNR/SSIM mandatory and expose LPIPS/FVD/VBench availability honestly.
2. Rebuild Type B loser selection with sharpness and blur gates.
3. Upgrade Type A LocalDPO-style metadata and keep it as the stable fallback.
4. Build `manifests/dpo_preference_protocol_v2_pairs.jsonl` without low-quality losers.
5. Run at most one DPO engineering smoke/run-through after v2 protocol passes, only to prove forward/backward/save/eval plumbing.

## Explicitly Not Run

- StageB is not run.
- GRPO is not run.
- Full-data long StageA is not run.
- Large-scale DPO is not run.
- Checkpoints, data, and weights are not deleted.
- MP4/JPG/PNG/HDF5/NPY/PT/checkpoints are not pushed.
