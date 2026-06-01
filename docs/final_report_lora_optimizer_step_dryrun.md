# Final Report: LoRA Optimizer-Step Dry-Run

## Gates

- Gate A: passed, LingBot-Fast 1-sample inference.
- Gate B: passed, 3 Fast rollouts.
- Gate C: partial/pass, camera embedding and strong stress camera effect passed; ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke, reward v5 ordering and RAFT/DINO real backend smoke passed, but generated depth/mask/physics remain incomplete.
- Gate E: passed for 1-pair optimizer-step dry-run on tiny camera-control LoRA.
- Gate F: no, real DPO training remains disallowed.

## Prior Art

Checked local adapter/config code and upstream VideoGPA/Wan references. VideoGPA uses a frozen reference, same-noise/timestep style DPO loss, PEFT LoRA in its trainers, and AdamW-style optimization. LingBot/Wan local plumbing already uses the real LingBot VAE, flow target `noise - x0`, frozen same-checkpoint reference, and camera-conditioned Plucker/control path.

This round used `AdamW` with lr `1e-5` because it matches the local low-LR adapter precedent and is conservative for a one-step smoke.

## Setup

- Actual remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_lora_optimizer_step_work`
- Branch: `physion-dpo-lora-optimizer-step-dryrun`
- Remote dry-run source commit: `0e1db995782116523e08293a8dd268e2fc9f6a44`
- `local_assets`: symlink to the shared main asset tree.
- Assets moved/deleted: no.
- Submitted assets/weights/videos/latents: no.
- Raw output path: `local_assets/outputs/smoke/lingbot_dpo_lora_optimizer_step_dryrun/`

## Optimizer-Step Dry-Run

- Status: passed.
- Pair count: `1`.
- Step count: `1`.
- Target modules: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank / alpha: `2 / 4.0`.
- Trainable params: `40,960`.
- Optimizer: `AdamW`, LoRA params only.
- Beta: `0.1`.
- `L_DPO_before`: `0.6931473016738892`.
- `E_policy_winner_before`: `0.8652127981185913`.
- `E_policy_loser_before`: `0.8322628140449524`.
- `E_ref_winner`: `0.8652140498161316`.
- `E_ref_loser`: `0.8322668075561523`.
- Grad norm before/after clipping: `1.4945835573598742e-05` / `1.4945835573598742e-05`.
- Optional recompute succeeded: `L_DPO_after=0.6931473016738892`.

## Parameter Safety

- LoRA params changed: yes, `4/4`, max abs diff `9.981580660678446e-06`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- Base params with grad: `0`.
- Reference params with grad: `0`.
- NaN/Inf gradients: no.
- Updated LoRA NaN/Inf: no.
- `restore_after_step`: passed, post-restore LoRA max diff `0.0`.
- LoRA saved: no.
- Checkpoint saved: no.
- LingBot weights modified: no.

## Memory

- GPU scope: only GPU 6/7 visible to the process.
- Peak PyTorch allocation: `54,482,460,672` bytes, about `50.75 GiB`.
- GPU 6/7 after run: idle, `1 MiB` each.
- OOM: no.

## Next Permission

Next round may do a 1-pair overfit mini-loop only if the user explicitly confirms it. Suggested bounds:

- same LoRA target modules only;
- rank `2`;
- at most 5 optimizer steps on the same pair;
- no checkpoint save;
- no LoRA save;
- no multi-pair training;
- compare before/after loss and restore/discard runtime adapter afterward.

Real DPO training is still not allowed.

## Next Minimal Action

If continuing DPO plumbing, ask before a 1-pair 5-step overfit mini-loop. If the user wants data work instead, only a 1-sample TDW generation dry-run should be considered. No real training yet.
