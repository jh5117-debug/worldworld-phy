# Prior Art: Fixed-Noise DPO Diagnostic

## Current Problem

The previous 1-pair / 5-step LoRA mini-loop passed with resampled noise and resampled timestep at each step. That proves repeated optimizer plumbing and safety, but the loss trend is not directly interpretable because each step uses a different denoising problem. This round fixes the noise and timestep so the same pair is optimized against the same DPO comparison for up to 10 steps.

## Files And Repos Checked

Remote third-party and local files checked:

- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-I2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX1.5-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- `local_assets/third_party/lingbot_world/generate.py`
- `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- `/home/nvme03/workspace/lingbot-world`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `configs/cam_physgeo/*.yaml`

The grep also touched a noisy LingBot download log with ANSI progress output. That raw output is not reproduced here; only relevant code findings are summarized.

## VideoGPA Noise / Timestep Handling

VideoGPA training scripts sample a fresh `timesteps = torch.randint(...)` and `noise = torch.randn_like(...)` inside the training step. The sampled noise/timestep are shared between winner and loser in a pair:

- CogVideo trainers call `scheduler.add_noise(x_win, noise, timesteps)` and `scheduler.add_noise(x_lose, noise, timesteps)`.
- The Wan2.2 trainer documents flow matching as `z_t = (1 - sigma) * z_0 + sigma * noise` and target velocity `noise - z_0`.
- Wan2.2 samples timesteps per step, computes sigma, uses the same noise for winner/loser, and optimizes LoRA with AdamW.

Therefore, same-noise/same-timestep within a pair is the preference-comparison invariant. Resampling between training steps is normal for training. Fixed noise/timestep across steps is a diagnostic, not the standard training recipe.

## Fixed-Noise Diagnostic Meaning

Fixed-noise/fixed-timestep keeps the denoising target identical across steps. This makes changes in:

- `Delta_policy = E_policy_loser - E_policy_winner`;
- preference logit `beta * (Delta_policy - Delta_ref)`;
- `L_DPO`;

more directly attributable to the LoRA update rather than to a new sampled denoising task.

The previous resampled run did not need monotonic loss decrease because each step solved a different noise/timestep problem. In this round, monotonic or near-monotonic loss movement is more interpretable, though a tiny rank-2 LoRA scope and very small learning rate may still produce a weak signal.

## This Round's Constraints

- Pair count: `1`.
- Max steps: `10`.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- LoRA target modules: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Optimizer: AdamW over LoRA params only.
- No checkpoint save.
- No LoRA save.
- No writeback to `local_assets/weights`.
- Reference remains frozen and under `torch.no_grad()`.
- Base parameters remain frozen.

## Safety And Sign Checks

The sign convention remains:

- energy is denoising/flow-target MSE;
- lower energy means the model assigns higher compatibility to a sample;
- `Delta = E_loser - E_winner`;
- larger `Delta_policy - Delta_ref` should lower the DPO loss.

The diagnostic is considered safe only if losses and gradients are finite, LoRA params change, base/reference stay unchanged, and no OOM occurs. If fixed-noise loss increases unexpectedly, inspect `Delta_policy`, `Delta_ref`, and the preference logit before changing the formula.

## Why This Is Still Not Training

This is a single-pair diagnostic with runtime LoRA and no saved adapter. It does not run VideoGPA `03_train.py`, does not use a dataloader, does not validate multi-pair generalization, and does not persist updates. Gate F real DPO training remains blocked.
