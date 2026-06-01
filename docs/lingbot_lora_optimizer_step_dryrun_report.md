# LingBot Tiny LoRA Optimizer-Step Dry-Run Report

## Result

Status: passed.

The 1-pair / 1-step optimizer-step dry-run ran on remote GPU 6/7 in:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_lora_optimizer_step_work`

Output path, not committed:

`local_assets/outputs/smoke/lingbot_dpo_lora_optimizer_step_dryrun/`

Raw log path:

`local_assets/outputs/smoke/lingbot_dpo_lora_optimizer_step_dryrun/stdout_stderr.log`

The raw log contains verbose model-load warnings from LingBot/Wan; the summary below uses the structured JSON outputs instead of reproducing that noisy text.

## Setup

- Branch used on remote: `physion-dpo-lora-optimizer-step-dryrun`
- Code commit used for remote dry-run: `0e1db995782116523e08293a8dd268e2fc9f6a44`
- `local_assets`: symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- GPUs visible to the run: `CUDA_VISIBLE_DEVICES=6,7`
- No rollout generation, reward calibration, Stage1, VideoGPA train, or formal DPO training was run.

## LoRA / Optimizer

- LoRA scope: `camera_control_lora_tiny`
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- Rank / alpha: `2 / 4.0`
- LoRA trainable params: `40,960`
- Optimizer: `AdamW`
- Learning rate: `1e-5`
- Optimizer param groups: `1`
- Optimizer params: `4` tensors, LoRA-only
- Max grad norm: `1.0`
- Optimizer steps executed: `1`
- LoRA factors are runtime-only and kept in fp32 so the single small AdamW step is numerically observable; the frozen LingBot base remains bf16 in the model path.

## Energies And Loss

- `E_policy_winner_before`: `0.8652127981185913`
- `E_policy_loser_before`: `0.8322628140449524`
- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_policy_before`: `-0.032949984073638916`
- `Delta_ref`: `-0.03294724225997925`
- `L_DPO_before`: `0.6931473016738892`
- `L_DPO_after` recompute: `0.6931473016738892`
- `Delta_policy_after`: `-0.03295034170150757`

The near-log(2) loss is expected because policy starts from the same base checkpoint as the frozen reference and this is only a one-step smoke.

## Gradient And Step Safety

- Grad norm before clipping: `1.4945835573598742e-05`
- Clip returned norm: `1.4945836483093444e-05`
- Grad norm after clipping: `1.4945835573598742e-05`
- NaN/Inf gradients: no
- LoRA params changed count: `4 / 4`
- LoRA max abs diff: `9.981580660678446e-06`
- LoRA mean abs diff: `2.9143903020667493e-06`
- Base sample params changed count: `0 / 12`
- Base sample max abs diff: `0.0`
- Reference sample params changed count: `0 / 8`
- Reference sample max abs diff: `0.0`
- Reference params with grad: `0`
- Base params with grad: `0`
- `restore_after_step`: passed; post-restore LoRA max abs diff `0.0`

## Memory

- GPU before: GPU 6/7 both `1 MiB`, idle.
- Peak allocated by PyTorch: `54,482,460,672` bytes, about `50.75 GiB`.
- Final GPU after: GPU 6/7 both `1 MiB`, idle.
- OOM: no.

## Files Written

Only local smoke outputs were written under `local_assets/outputs/smoke/lingbot_dpo_lora_optimizer_step_dryrun/`:

- `summary.json`
- `grad_summary.json`
- `param_diff_summary.json`
- `command.txt`
- `stdout_stderr.log`
- `gpu_before.txt`
- `gpu_after.txt`
- condition summaries for reference/policy before/policy after

No `.pt`, `.pth`, `.safetensors`, `.bin`, checkpoint, or saved LoRA file was written in the dry-run output directory.

## Gate Decision

Gate E optimizer-step dry-run: passed.

Gate F real DPO training: still no. The next possible action is only a user-confirmed 1-pair overfit mini-loop, for example 5 optimizer steps on the same pair, still no checkpoint and no LoRA save.
