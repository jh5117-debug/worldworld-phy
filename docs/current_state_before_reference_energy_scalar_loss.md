# Current State Before Reference Energy / Scalar Loss

## Execution Context

- Local implementation worktree: `/tmp/local_assets_work`
- Branch: `physion-reference-energy-dpo-scalar-dryrun`
- Base commit: `f4483b1cb4bb969fea699e291432e56e009b073b`
- Remote execution worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_energy_forward_work`
- Remote `local_assets`: symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- No data, weight, latent, HDF5, MP4, NPY/NPZ, PT/PTH, safetensors, or logs are intended for git.

## Prior Gate State

- Policy energy passed.
- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- Target type: `flow_velocity_noise_minus_x0`
- Target evidence: LingBot `sample_flow_batch`, VideoGPA Wan2.2 flow matching script, and LingBot inference conversion comments.
- Reference energy: deferred before this round.
- DPO scalar loss: not run before this round.

## Batch / Condition

- Batch path: `local_assets/outputs/smoke/lingbot_dpo_batch_dryrun`
- Batch tensors: `batch_tensors.pt`
- Winner/loser latent shape: `[16, 2, 60, 104]`
- Same noise: confirmed.
- Same timestep: confirmed.
- Earlier example timestep: `579`; latest rerun used `176`.
- Condition keys include prompt, image, poses, intrinsics, metadata, and dummy action compatibility.
- Plucker/control tensor shape: `[1, 384, 2, 60, 104]`
- Dummy action norm: `0.0`
- `use_action=false`: preserved.

## This Round Permission

Allowed:

- 1-pair frozen-reference energy dry-run.
- 1-pair scalar DPO loss dry-run only if reference energy is finite.
- Physion/TDW generation prior-art review and plan.

Not allowed:

- Training.
- Backward.
- Optimizer.
- LoRA save.
- VideoGPA `03_train.py`.
- Stage1.
- New rollout generation.
- Reward calibration.
- Large TDW/Physion generation.
