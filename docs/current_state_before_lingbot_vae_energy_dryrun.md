# Current State Before LingBot VAE / Energy Dry-Run

## Execution Context

- Local coding worktree: `/tmp/local_assets_work`
- Remote execution worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_videogpa_encode_work`
- Requested project root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`
- Remote helper worktree uses the same `local_assets` symlink/assets as the project root; no data, weights, videos, latents, HDF5, NPY, PT, or safetensors were moved or deleted.
- Base branch before this round: `physion-videogpa-encode-smoke`
- Local branch for this round: `physion-lingbot-vae-energy-dryrun`
- Base commit: `531e8198e65ceed8caf0dd3cf3ac63755ee02a2e`

## Previous VideoGPA State

- VideoGPA official repo: `local_assets/third_party/VideoGPA/official_repo`
- VideoGPA official commit reported by prior inspect: `551e63a5c2c493962f1e1d090bfa8324bf18b694`
- Native encode scripts found previously: CogVideoX, CogVideoX-I2V, CogVideoX1.5, and Wan2.2 TI2V.
- Native VideoGPA encode does not natively preserve LingBot-Fast camera poses/intrinsics.
- `gt_vs_corrupt` tiny builder produced 0 accepted pairs and 10 rejected rows; no fake empty pair was generated.
- `gt_vs_fast_rollout` produced 2 pairs from reward v5.
- Winner/loser video paths, prompt, condition image, poses, intrinsics, metadata, and `use_action=false` were readable.
- Camera condition was preserved as `extra_condition` plus sidecar JSON.
- Native latent encode stayed partial because using a VideoGPA-native VAE would not prove LingBot-Fast compatibility.

## Adapter State Before This Round

Implemented before this round:

- `encode_condition` metadata/shape dry-run.
- `collate_winner_loser_batch` metadata dry-run.

Still blocked before this round:

- `load_policy_model`
- `load_reference_model`
- `load_vae`
- `encode_video_to_latent`
- `sample_same_noise_timestep`
- `compute_dpo_energy_or_logprob`

This round allowed only 1-pair dry-run plumbing. Training, DPO optimization, VideoGPA `03_train.py`, Stage1, rollout generation, and reward calibration remained disallowed.

