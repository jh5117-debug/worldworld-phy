# Final Report: Fixed-Noise 1-Pair DPO Diagnostic

## Gates

- Gate A: passed, LingBot-Fast 1-sample inference.
- Gate B: passed, 3 Fast rollouts.
- Gate C: partial/pass, camera embedding and stress video effect passed; ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke, reward v5 clean > Fast with RAFT + DINO, but generated depth/mask/physics remain incomplete.
- Gate E: passed for fixed-noise/fixed-timestep 1-pair diagnostic at plumbing/safety level.
- Gate F: no, real DPO training remains disallowed.

## Prior Art

Checked VideoGPA `03_train.py` scripts, `train/loss.py`, LingBot/Wan optimizer/inference examples, and local adapter/config code. VideoGPA samples fresh noise/timestep per training step, but shares that same noise/timestep between winner and loser. That supports same-noise pair comparison as the invariant.

Fixed noise/timestep is not the normal VideoGPA training recipe. It is a diagnostic that makes loss and `Delta_policy` changes more interpretable by removing per-step denoising-task variation. No checkpoint or LoRA save path from VideoGPA was used.

## Setup

- Actual remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_fixed_noise_diagnostic_work`
- Remote branch: `physion-dpo-fixed-noise-diagnostic`
- Remote code commit for the run: `2847c27`
- Final pushed branch-tip commit: this report commit; verify with `git rev-parse HEAD` after checkout.
- `local_assets`: untracked symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- Assets moved/deleted: no.
- Submitted assets/weights/videos/latents: no.
- Output path, not committed: `local_assets/outputs/smoke/lingbot_dpo_1pair_overfit_miniloop_fixed_noise/`
- Raw log path: `local_assets/outputs/smoke/lingbot_dpo_1pair_overfit_miniloop_fixed_noise/runner_stdout_stderr.log`

## Configuration

- Pair count: `1`.
- Steps: `10`.
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- LoRA rank / alpha: `2 / 4.0`
- Trainable LoRA params: `40,960`.
- Optimizer: `AdamW`, LoRA params only.
- Learning rate: `1e-5`.
- Beta: `0.1`.
- Max grad norm: `1.0`.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- Noise resampled each step: no.
- Timestep resampled each step: no.
- LoRA save: no.
- Checkpoint save: no.

## Per-Step Metrics

| step | L_DPO | Delta_policy | Delta_ref | preference logit | grad_norm | LoRA max diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.6931471229 | -0.0061962008 | -0.0061976612 | 1.460314e-07 | 2.005005e-05 | 9.986965e-06 |
| 1 | 0.6931471825 | -0.0061974525 | -0.0061976612 | 2.086163e-08 | 1.989856e-05 | 1.997287e-05 |
| 2 | 0.6931471825 | -0.0061977357 | -0.0061976612 | -7.450581e-09 | 2.002210e-05 | 2.995986e-05 |
| 3 | 0.6931471825 | -0.0061977357 | -0.0061976612 | -7.450581e-09 | 2.035400e-05 | 3.995268e-05 |
| 4 | 0.6931472421 | -0.0061987042 | -0.0061976612 | -1.043081e-07 | 2.083059e-05 | 4.995591e-05 |
| 5 | 0.6931471825 | -0.0061976463 | -0.0061976612 | 1.490116e-09 | 2.148054e-05 | 5.997223e-05 |
| 6 | 0.6931472421 | -0.0061984062 | -0.0061976612 | -7.450581e-08 | 2.211122e-05 | 7.000639e-05 |
| 7 | 0.6931472421 | -0.0061984807 | -0.0061976612 | -8.195639e-08 | 2.306217e-05 | 8.014392e-05 |
| 8 | 0.6931471825 | -0.0061971694 | -0.0061976612 | 4.917383e-08 | 2.385222e-05 | 9.035715e-05 |
| 9 | 0.6931471825 | -0.0061972886 | -0.0061976612 | 3.725290e-08 | 2.473369e-05 | 1.006147e-04 |

All losses and gradients were finite. Every row used timestep `[579]` with fixed noise.

## Trend

- `loss_first`: `0.6931471228599548`
- `loss_last`: `0.6931471824645996`
- `loss_min`: `0.6931471228599548`
- `loss_max`: `0.6931472420692444`
- `loss_delta`: `+5.960464477539063e-08`
- Monotonic non-increasing: no.
- `Delta_policy` delta last minus first: `-1.087784767150879e-06`
- Preference logit delta last minus first: `-1.0877847955725883e-07`

The fixed diagnostic is interpretable, but the overfit signal is weak. LoRA parameters move consistently, yet the loss remains effectively at `log(2)` and does not monotonically decrease. This is likely because policy/reference start from identical weights, the LoRA scope is tiny, and lr is deliberately conservative.

## Sign Check

The sign convention is consistent:

- energy is MSE to the LingBot flow target;
- lower energy means better compatibility;
- `Delta = E_loser - E_winner`;
- positive `beta * (Delta_policy - Delta_ref)` lowers DPO loss.

The observed preference logits are tiny and fluctuate around zero. The small non-monotonic loss movement is not evidence of a sign flip; it is a weak-signal result.

## Safety

- Status: passed.
- Steps completed: `10 / 10`.
- OOM: no.
- Peak PyTorch allocation: `54,490,291,712` bytes, about `50.77 GiB`.
- LoRA params changed: yes, `4 / 4`.
- Final LoRA max abs diff: `0.0001006147067528218`.
- Final LoRA mean abs diff: `4.416457340994384e-05`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- Base params with grad: `0`.
- Reference params with grad: `0`.
- NaN/Inf gradients: no.
- Updated LoRA NaN/Inf: no.
- `restore_after_loop`: passed; post-restore LoRA max diff `0.0`.
- No checkpoint saved.
- No LoRA saved.
- No files were written under `local_assets/weights`.
- Final GPU check: GPU 6/7 both `1 MiB`, `0%`.

The output directory contains JSON/log summaries and condition sidecar `poses.npy` / `intrinsics.npy` / dummy `action.npy` files under `local_assets/outputs/smoke`; none are tracked or submitted to git.

## Next Permission

Next round may consider a 5-pair or 10-pair tiny overfit smoke only with explicit user confirmation. Given the weak fixed-noise signal, a stronger fixed-noise sensitivity diagnostic, for example a slightly higher LoRA lr or a fixed pair with more steps, may be more informative before expanding pair count.

Real DPO training remains not allowed.

## Next Minimal Action

If continuing DPO plumbing, ask before either a stronger fixed-noise sensitivity run or a 5-pair/10-pair tiny overfit smoke. If the user wants data work instead, only a 1-sample TDW generation dry-run should be considered. Still no real training.
