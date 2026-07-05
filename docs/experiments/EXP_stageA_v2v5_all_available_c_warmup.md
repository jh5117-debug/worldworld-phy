# EXP StageA V2V-5 All-Available C-Scope Warmup

## Current Status

The requested 4900/100 split was unavailable; current disk state has 3299 unique Stage1-ready generated_v5 clips. User approved using all available data.

## Goal

Run V2V-5 prefix-aware StageA warmup on all currently available Stage1-ready clips, then use the resulting C-scope LoRA checkpoint to regenerate and audit 500 loser pairs.

## Input Data

- Train: 3299 unique generated_v5 Stage1-ready clips
- Val/test: 100 mirrored rows for monitoring only
- No held-out claim is made because all usable clips are included in warmup training.

## LoRA Scope

C scope from the loser-source decision:

- camera_conditioning + self_attention
- last 4 blocks only
- rank 4
- alpha 4
- dropout 0.05

## Training Configuration

- Config: `configs/cam_physgeo/fast_stageA_v2v5_C_camera_self_last4_r4_all_available_2epoch.yaml`
- Launcher: `scripts/launch_fast_stageA_v2v5_C_all_available_2epoch.sh`
- Precision: bf16 mixed-safe
- GPUs: physical GPU4,5,6,7
- num_epochs: 2
- grad accumulation: 4
- optimizer steps: 414
- save/eval interval: 103 steps

## Success Gate

- training starts on GPU4-7 only
- no GPU0-3 usage
- no OOM/SIGFPE/NaN
- checkpoints saved at expected intervals
- final adapter present
- fixed-val metrics written
- logs show prefix-aware V2V-5 training path, no image-only fallback

## Post-Warmup Loser Regeneration Plan

After warmup completes:

1. Use final or best checkpoint as new C loser-source model.
2. Generate candidate losers for 500 DPO pairs.
3. For every candidate: build contact sheet, compute metrics/reward, and Codex visually audit.
4. Reject black/collapsed/too blurry/too subtle/too artificial failures.
5. Produce repaired ready500 manifest and PPT/QA notes.

## Cleanup Plan

First produce a cleanup inventory. Do not delete raw data, weights, checkpoints, or local assets needed for reproducibility. Only delete explicitly safe temp/log/cache files after they are listed.

## What Is Not Run

- no DPO training
- no SDPO
- no Linear-DPO
- no winner-anchor
- no StageB
- no GRPO
- no broad-LoRA
- no checkpoint deletion
- no data/weights/video push
