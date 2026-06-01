# Final Report: 1-Pair LoRA DPO Overfit Mini-Loop

## Gates

- Gate A: passed, LingBot-Fast 1-sample inference.
- Gate B: passed, 3 Fast rollouts.
- Gate C: partial/pass, camera embedding and stress video effect passed; ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke, reward v5 clean > Fast with RAFT + DINO, but generated depth/mask/physics remain incomplete.
- Gate E: passed for 1-pair 5-step runtime LoRA mini-loop dry-run.
- Gate F: no, real DPO training remains disallowed.

## Prior Art

Checked remote `local_assets/third_party/VideoGPA/official_repo/train/*/03_train.py`, `train/loss.py`, `train/dataset.py`, LingBot `generate.py`, Wan/LingBot inference code, and local adapter/config files. VideoGPA trainers use LoRA, AdamW, step-wise training loops, optional gradient checkpointing, and checkpoint/final-LoRA saving. This round reused only the minimal loop structure; checkpoint/save behavior stayed disabled.

LingBot/Wan local code supports LoRA-style adapter loading for inference and uses the same camera/control path already proven in prior gates. The mini-loop stays runtime-only and does not modify LingBot weight files.

## Setup

- Actual remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_1pair_overfit_miniloop_work`
- Branch used remotely: `physion-dpo-1pair-overfit-miniloop`
- Remote code commit used: `b302f13`
- `local_assets`: untracked symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- Assets moved/deleted: no.
- Submitted assets/weights/videos/latents: no.
- Output path, not committed: `local_assets/outputs/smoke/lingbot_dpo_1pair_overfit_miniloop/`
- Raw log path: `local_assets/outputs/smoke/lingbot_dpo_1pair_overfit_miniloop/stdout_stderr.log`

## Mini-Loop Configuration

- Pair count: `1`.
- Steps: `5`.
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- LoRA rank / alpha: `2 / 4.0`
- Trainable LoRA params: `40,960`.
- Optimizer: `AdamW`, LoRA params only.
- Learning rate: `1e-5`.
- Beta: `0.1`.
- Max grad norm: `1.0`.
- Noise resampled each step: yes.
- Timestep resampled each step: yes.
- Same noise/timestep between winner and loser within each step: yes.
- LoRA save: no.
- Checkpoint save: no.

## Per-Step Metrics

| step | timestep | L_DPO | E_policy_w | E_policy_l | E_ref_w | E_ref_l | Delta_policy | Delta_ref | grad_norm | LoRA max diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 473 | 0.6931473017 | 0.2602852285 | 0.2429418415 | 0.2602841556 | 0.2429428548 | -0.0173433870 | -0.0173413008 | 4.198763e-05 | 9.995572e-06 |
| 1 | 15 | 0.6931471229 | 1.0679484606 | 1.0655075312 | 1.0679491758 | 1.0655066967 | -0.0024409294 | -0.0024424791 | 3.579057e-05 | 1.997493e-05 |
| 2 | 649 | 0.6931470633 | 0.0777912587 | 0.0768671930 | 0.0777912289 | 0.0768649951 | -0.0009240657 | -0.0009262338 | 2.626446e-05 | 2.995473e-05 |
| 3 | 999 | 0.6931471229 | 0.0825148076 | 0.0485249348 | 0.0825156420 | 0.0485247262 | -0.0339898728 | -0.0339909159 | 2.689276e-05 | 3.951875e-05 |
| 4 | 212 | 0.6931472421 | 0.7667696476 | 0.7369114161 | 0.7667655945 | 0.7369086742 | -0.0298582315 | -0.0298569202 | 4.320003e-05 | 4.924209e-05 |

All five losses and gradients were finite. Clipping did not materially change the grad norms because they were already far below `1.0`.

## Safety

- Status: passed.
- Steps completed: `5 / 5`.
- OOM: no.
- Peak PyTorch allocation: `54,486,292,992` bytes, about `50.75 GiB`.
- LoRA params changed: yes, `4 / 4`.
- Final LoRA max abs diff from initial: `4.924208769807592e-05`.
- Final LoRA mean abs diff from initial: `1.6316957135131817e-05`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- Base params with grad: `0` each step.
- Reference params with grad: `0`.
- NaN/Inf gradients: no.
- Updated LoRA NaN/Inf: no.
- `restore_after_loop`: passed; post-restore LoRA max diff `0.0`.
- No checkpoint saved.
- No LoRA saved.
- No files were written under `local_assets/weights`.
- Final GPU check: GPU 6/7 both `1 MiB`, `0%`.

The output directory contains JSON/log summaries and condition sidecar `poses.npy` / `intrinsics.npy` / dummy `action.npy` files under `local_assets/outputs/smoke`; none are tracked or submitted to git.

## Interpretation

The repeated mini-loop shows a real, finite DPO plumbing signal and persistent LoRA-only parameter movement. The loss stays near `log(2)`, which is expected because policy and reference start from the same checkpoint and each step resamples noise/timestep. Therefore the loss trend is not a monotonic overfit proof. The observable signal is:

- finite policy/reference energies across five different timesteps;
- finite gradients on all four LoRA tensors;
- LoRA parameter diff grows over steps;
- base/reference remain unchanged;
- no OOM.

Fixed-noise/fixed-timestep comparison was not run to keep this round scoped after the full 5-step smoke completed.

## Next Permission

Next round may consider a tiny 5-pair or 10-pair overfit smoke only with explicit user confirmation. Constraints should remain:

- LoRA-only optimizer;
- no checkpoint save;
- no LoRA save unless separately approved;
- no VideoGPA `03_train.py`;
- no multi-pair real training loop;
- keep base/reference immutable checks.

Real DPO training remains not allowed.

## Next Minimal Action

If continuing DPO plumbing, ask before either a fixed-noise 1-pair diagnostic or a 5-pair/10-pair tiny overfit smoke. If the user wants data work instead, only a 1-sample TDW generation dry-run should be considered. Still no real training.
