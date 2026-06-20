# StageA v5 Code and Lineage Audit

Date: 2026-06-20

## Scope

This audit covers the StageA camera-conditioned LingBot-Fast warmup path for the TDW / Physion v5 data line. It does not run DPO, reward scoring, pair construction, rollout candidate generation, StageB, GRPO, PhyInOne, CSGO, or VideoGPA 03_train.

## Current Code Lineage

- Entry point: `physical_consistency.stages.stage1_physinone_cam.runner`.
- Branch trainer: `physical_consistency.stages.stage1_physinone_cam.trainer.Stage1BranchTrainer`.
- Dataset class: `physical_consistency.stages.stage1_physinone_cam.dataset.PhysInOneCamDataset`.
- LingBot/Wan runtime helper: `physical_consistency.trainers.stage1_components.LingBotStage1Helper`.
- LoRA wrapper: `physical_consistency.trainers.stage1_components.LoRALinear`.

## Key Findings

1. The old `cam_physgeo.training.train_stage1_warmup` wrapper only forwards to the legacy Stage1 runner and previously used a wrapper-level `max_steps` environment variable. The real step semantics must live in `Stage1PhysInOneConfig` and `Stage1BranchTrainer`.
2. The true training step is not a placeholder. It decodes batches, encodes target video with VAE, encodes text, builds Plucker camera control from poses/intrinsics, samples a timestep, computes flow target `noise - video_latent`, forwards the Wan model, and backpropagates MSE.
3. The old LoRA matcher was too coarse: it selected Linear layers by `target_prefixes=("blocks",)` and `block_start`, without explicitly reporting self-attention, cross-attention, FFN, or camera-conditioning groups.
4. The Stage1 dataset expects a directory with `metadata_train.csv`, `metadata_val.csv`, and per-clip `video.mp4`, `poses.npy`, `intrinsics.npy`. LingBot JSONL manifests must be prepared into this format before training.
5. The active `generated_v5` TDW scale-up currently has raw HDF5 only. It has no LingBot conversion outputs (`target.mp4`, `poses.npy`, `intrinsics.npy`) under `generated_v5`, so it is not directly trainable by Stage1.

## Implemented Repairs

- Added broad-LoRA target groups:
  - `camera_conditioning`
  - `self_attention`
  - `cross_attention`
  - `ffn`
- Added required-group checks; training fails if any required group is empty.
- Added module group metadata to `model._pc_lora_config` and `model._pc_lora_target_report`.
- Added real optimizer-step fields:
  - `max_train_optimizer_steps`
  - `min_train_optimizer_steps`
  - `save_every_optimizer_steps`
  - `scheduler_eta_min`
- Added adapter-only artifact save as `adapter_state.pt` plus `adapter_metadata.json`.
- Added Stage1 dataset preparation from LingBot JSONL manifests.
- Added generated_v5 immutable snapshot tool that preserves validation status and does not mark blocked chunks as usable.

## Current Blocker

The existing `generated_v5` validation reports show generated HDF5 files but `Validation ok count: 0`, with row status `blocked`. Under the current safety rules, these samples must not be used for formal StageA training until validation is repaired or rerun successfully.

## TDW Safety

The active TDW scale-up sessions are protected:

- `tdw_v5_4000_gpu0_scaleup`
- `tdw_v5_4000_monitor`

StageA code and tests must use GPUs other than GPU0. No command should attach, kill, restart, or send keys to those tmux sessions.
