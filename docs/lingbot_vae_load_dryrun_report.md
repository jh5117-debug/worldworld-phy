# LingBot VAE Load Dry-Run Report

## Result

- Status: passed.
- VAE class: `Wan2_1_VAE`
- VAE module: `local_assets/third_party/lingbot_world/wan/modules/vae2_1.py`
- VAE checkpoint: `local_assets/cache/lingbot_fast_cam_runtime/Wan2.1_VAE.pth`
- Init pattern: `vae_pth_device`
- Device: `cuda` with `CUDA_VISIBLE_DEVICES=6,7`
- Requested dtype: `bf16`
- Load time: approximately 17-18 seconds.

## GPU Memory

- VAE-only memory after load: about 264 MB allocated, about 539 MB reserved.
- Peak during VAE load: about 531 MB allocated.
- During full pair encode, peak allocation reached about 6.5 GB and reserved memory reached about 8.9 GB.

## Blockers

- None for VAE loading.
- VideoGPA native VAE remains intentionally unused because it would not prove LingBot-Fast latent compatibility.

## Next

VAE load success allowed the 1-pair winner/loser latent encode smoke.

