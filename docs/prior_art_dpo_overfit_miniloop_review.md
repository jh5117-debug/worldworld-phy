# Prior Art: DPO 1-Pair Overfit Mini-Loop

## Current Problem

The previous smoke proved that one AdamW step can update only runtime LoRA parameters on the LingBot-Fast camera-control path while leaving base and reference parameters unchanged. This round checks a bounded 5-step loop on the same pair. It is still only a plumbing/stability dry-run: no trainer, no checkpoint, no saved LoRA, no multi-pair DPO.

## Files And Repos Checked

Remote third-party and local project files checked:

- `local_assets/third_party/VideoGPA/official_repo/train/01_preference_pair.py`
- `local_assets/third_party/VideoGPA/official_repo/train/dataset.py`
- `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-I2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX1.5-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/replicate.py`
- `local_assets/third_party/lingbot_world/generate.py`
- `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `cam_physgeo/dpo/lora_utils.py`
- `configs/cam_physgeo/stage1_warmup.yaml`
- `configs/cam_physgeo/stage2_anchored_dpo.yaml`

The local checkout under `/tmp/local_assets_work` does not contain the full third-party asset repos, so third-party inspection was performed on the remote shared asset worktree. No external model download was performed.

## VideoGPA Training Loop References

VideoGPA organizes work into preference pair export, latent encode, and `03_train.py` trainers. The official trainers use PEFT LoRA and Lightning-style training loops. The CogVideo and Wan trainers define LoRA ranks/targets, create an optimizer with `torch.optim.AdamW`, use a per-step scheduler, enable gradient checkpointing in larger runs, save periodic checkpoints, and save final LoRA adapters.

For this round, only the loop shape is relevant:

- each step zeros gradients;
- computes model/reference prediction errors;
- computes DPO loss;
- backpropagates;
- applies optional gradient clipping in the trainer framework;
- runs one optimizer step;
- logs per-step metrics.

The checkpoint and final LoRA save portions are intentionally not reused.

## LingBot / Wan References

LingBot local inference supports loading LoRA checkpoints through `generate.py`. That code imports LoRA injection helpers from `scripts.train_lingbot_dpo_lora`, can inject LoRA targets such as control/self-attention, sets LoRA active, and keeps the loaded model in eval mode for generation.

Our current adapter uses a stricter runtime-only scope:

- model: LingBot-Fast `WanModelFast` through `WanI2VFast`;
- target: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- LoRA rank / alpha: `2 / 4.0`;
- flow target: `noise - x0`;
- reference: same LingBot-Fast checkpoint, frozen and evaluated under `torch.no_grad()`;
- condition: same prompt/image/camera Plucker/control sidecar, with `use_action=false` and dummy action compatibility only.

## Why 5 Steps Only

Five steps are enough to test whether the one-step plumbing remains stable when repeated:

- finite scalar loss on every step;
- finite gradients on LoRA params;
- LoRA params continue changing;
- base/reference remain unchanged;
- no OOM;
- no checkpoint or adapter save.

This does not test convergence, data diversity, or real training stability.

## Noise And Timestep Policy

This round uses:

- fixed same pair;
- same winner/loser condition per step;
- same noise and same timestep between winner and loser within a step;
- resampled noise each step;
- resampled timestep each step.

Because noise/timestep are resampled across steps, the DPO loss is not expected to decrease monotonically. A fixed-noise/fixed-timestep comparison can be a future diagnostic if needed.

## Safety Plan

The mini-loop must:

- inject runtime LoRA only into the two selected camera-control modules;
- freeze all non-LoRA policy params;
- load reference frozen with `requires_grad=False`;
- put only LoRA params in AdamW;
- run exactly `num_steps <= 5`;
- execute no more than 5 `optimizer.step()` calls;
- clip grad norm at `1.0`;
- write only JSON/text smoke summaries under `local_assets/outputs/smoke`;
- save no LoRA, no checkpoint, no model weights;
- verify base/reference sample parameter diffs remain zero;
- optionally restore runtime LoRA params after the loop.

## Why This Is Not Real Training

The run uses one pair, no dataloader, no checkpointing, no adapter save, no multi-pair sampling, no validation, and no persistent parameter update. It only validates Gate E mini-loop plumbing. Gate F real DPO training remains blocked until explicitly approved in a later round.
