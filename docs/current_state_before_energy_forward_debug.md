# Current State Before Energy Forward Debug

## Location

- Intended remote project: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`
- Main remote worktree is dirty and remains untouched for edits.
- Development branch for this round: `physion-lingbot-energy-forward-debug`
- Base commit: `d0b6a244a41919f0446f530f4b52e20b9a31db30`

## Previous Gate E State

- VAE load: passed with real `Wan2_1_VAE`.
- Winner latent shape: `[16, 2, 60, 104]`.
- Loser latent shape: `[16, 2, 60, 104]`.
- Condition keys: image, prompt, poses, intrinsics, metadata, dummy action, and `use_action=false`.
- Plucker/control tensor shape: `[1, 448, 2, 60, 104]` in the previous shape dry-run.
- Dummy action norm: `0.0`.
- Same noise: confirmed.
- Same timestep: confirmed.
- Previous timestep example: `579`.
- Reward margin: `0.5240882262358174`.

## Energy Blocker

The previous adapter intentionally left `compute_dpo_energy_or_logprob` as
`NotImplementedError` because it had not yet wired LingBot-Fast's real
denoising / velocity / flow-matching forward target. This round is allowed to
attempt only a 1-pair no-backward/no-optimizer energy dry-run.

## Training Permission

- Real training: no.
- DPO optimization: no.
- VideoGPA `03_train.py`: no.
- Stage1: no.
- New rollout generation: no.
- This round: only 1-pair forward/energy plumbing dry-run.
