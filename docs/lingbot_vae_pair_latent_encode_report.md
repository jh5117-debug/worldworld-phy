# LingBot VAE Pair Latent Encode Report

## Result

- Status: passed.
- Pair id: `pair_2a77384981ab`
- Pair type: `gt_vs_fast_rollout`
- Winner video: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke/physion_movingcam_07abddf5748b/target.mp4`
- Loser video: `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_07abddf5748b/generated.mp4`
- Output directory: `local_assets/outputs/smoke/lingbot_vae_encode/pair_2a77384981ab/`
- Winner latent path: `local_assets/outputs/smoke/lingbot_vae_encode/pair_2a77384981ab/winner_latent.pt`
- Loser latent path: `local_assets/outputs/smoke/lingbot_vae_encode/pair_2a77384981ab/loser_latent.pt`
- Condition sidecar path: `local_assets/outputs/smoke/lingbot_vae_encode/pair_2a77384981ab/condition_sidecar.json`

## Latent Shapes

- Input tensor shape for both videos: `[3, 8, 480, 832]`
- Winner latent shape: `[16, 2, 60, 104]`
- Loser latent shape: `[16, 2, 60, 104]`
- Latent dtype returned by VAE: `float32`
- Latent device during encode: `cuda:0` under `CUDA_VISIBLE_DEVICES=6,7`
- Inferred temporal compression: `4x`
- Inferred spatial compression: `8x`
- NaN/Inf: none detected for winner or loser.

## Statistics

- Winner latent mean/std: `-0.0452 / 0.5787`
- Winner latent min/max: `-2.9673 / 2.8279`
- Loser latent mean/std: `-0.0372 / 0.5229`
- Loser latent min/max: `-2.6242 / 3.1768`
- Winner encode time: about `2.51s`
- Loser encode time: about `0.80s`
- VAE load time inside encode: about `17.07s`
- Peak CUDA allocation during pair encode: about `6.50 GB`

## Decode

- Decode/reconstruction was not attempted because the adapter has not wired a LingBot decode smoke path yet.
- This is a LingBot-compatible latent encode smoke, not a reconstruction-quality test.

## Metadata

- Camera metadata was preserved in the sidecar.
- No latent files were added to git.

