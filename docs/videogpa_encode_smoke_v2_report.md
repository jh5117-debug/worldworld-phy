# VideoGPA Encode Smoke V2 Report

## Status

- Result: partial.
- Pair JSON readable: yes.
- Winner/loser videos readable: yes.
- Encode attempted: no.
- Encoded pair count: `0`.
- Latent output path: none.
- Latent shape: none.

## Why No Latent Was Written

The official VideoGPA repo has native CogVideoX and Wan2.2 encode scripts, but those scripts expect their own backend VAE/model configuration. LingBot-Fast uses project-local WanI2VFast, companion LingBot VAE/T5 assets, and camera Plucker conditioning. A LingBot-specific VAE and condition adapter is not implemented yet, so claiming a real latent encode would be misleading.

## Preserved Sidecars

Sidecars were written under:

`local_assets/outputs/smoke/videogpa_encode_gt_vs_fast/sidecars/`

Each sidecar preserves:

- prompt;
- condition image path;
- `poses.npy`;
- `intrinsics.npy`;
- `metadata.json`;
- `use_action=false`;
- winner/loser video paths;
- reward metadata.

## Compatibility Notes

- Prompt preserved: yes.
- Image condition preserved: yes.
- Poses/intrinsics preserved: yes, as sidecar metadata.
- LingBot-specific VAE needed: yes.
- Native VideoGPA VAE compatibility with LingBot-Fast: not established.
- This is encode-readiness smoke, not DPO training readiness.
- Trainer adapter cannot start until real LingBot latent encode and real energy/logprob are implemented.

## DPO Status

DPO remains blocked. No DPO train command was run.
