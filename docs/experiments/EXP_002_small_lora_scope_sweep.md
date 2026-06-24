# EXP_002 Small-LoRA Scope Sweep

Updated: 2026-06-24 12:47:51 CST  
Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`  
Branch: `research/quant-small-lora-dpo-probe-20260624`  
Start commit: `63d1b93`  

This PRD is written before experiment launch. It must be updated after results are parsed and before the next stage is considered complete.


## Problem and Hypothesis

Broad-LoRA over 560 Linear layers degraded generation despite fixed-val loss improvement. A smaller scope may preserve LingBot-Fast visual priors while improving camera/background consistency.

Hypothesis: camera-only or limited attention LoRA with low rank can avoid foreground/physics degradation seen in broad-LoRA.

## Unique Variable

LoRA scope/rank only. Dataset, prompt, sample order seed, training length, optimizer, and inference settings are held fixed across A/B/C/D.

## Source Model

Original LingBot-Fast: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`.

## Data Manifest and SHA256

Use one immutable current stage1-ready generated_v5 snapshot. If full 5000 is not ready, use current stage1-ready partial snapshot with explicit partial label and template/camera-aware sampler.

## LoRA Scopes

A. camera-only, rank=4, alpha=4.  
B. camera-only, rank=8, alpha=8.  
C. camera conditioning + limited self/temporal attention Q/K/V/O, rank=4, selected blocks only.  
D. camera conditioning + limited cross-attention Q/K/V/O, rank=4, selected blocks only.

No FFN LoRA. No all-block broad-LoRA. Trainable params must be far below 102,891,520.

## Optimizer / Steps

- high-noise-only
- LR: 1e-6 or 2e-6 after preflight selection
- warmup: 5%
- checkpoints: 0 / 50 / 100 / 200 optimizer steps
- max steps: 200
- fixed val every 50
- 81 frames
- BF16 mixed-safe per StageA readiness

## GPU Mapping

A: GPU0,1. B: GPU2,3. C: GPU4,5. D: GPU6,7. Each uses `nproc_per_node=2`, gradient accumulation 4, effective global batch about 8.

## Preflight

Each scope must pass a true 5-step LingBot-Fast preflight before full 200-step sweep. Required: adapter loaded, loss finite, gradients nonzero, adapter save/load, no OOM/SIGFPE/NaN.

## Evaluation

For step0/50/100/200, generate a 16-condition probe. After sweep, evaluate selected checkpoints on Quant Benchmark v1.

## Success Gate

At least one scope must improve BRC or CAF vs Original Fast without >2% drop in FG-ID/Quality, without increased freeze/disappearance/duplication, and with Codex audit total not below Original Fast. If none pass, no new model is selected.

## Outputs

- `local_assets/experiments/small_lora_scope_sweep_<timestamp>/`
- `docs/small_lora_scope_sweep_final_report.md`
- `reports/video_audit/small_lora_scope_sweep/`

## Stop Conditions

Stop a scope on OOM, NaN/Inf, required group match=0, or repeated severe visual collapse. Continue other scopes.

## Git Commit

Pre-launch PRD commit: `Add quantitative benchmark and small-LoRA sweep PRDs`.

## Status


## 2026-06-24 Preflight Data-Gate Fix

First preflight attempt failed before optimizer steps because the Stage1 dataset preparation helper generated bad symlinks (`video.mp4 -> .`) for generated_v5 manifests. The helper now supports `target_video`, `poses`, and `intrinsics`, rejects empty paths, and reads prompt text from prompt files. A fixed immutable dataset view was prepared at:

`local_assets/experiments/small_lora_scope_sweep_20260624/stage1_dataset_fullprep_20260624_0152_fixed/`

The fixed view contains train/val/test = 2804/329/166 and sampled rows decode correctly. The sweep remains BLOCKED until the four 5-step preflights pass on this fixed view.


PREFLIGHT_PASS; READY_FOR_200_STEP_SWEEP.


## 2026-06-24 Preflight Result

Status: PREFLIGHT_PASS_FOR_ALL_FOUR_SCOPES.

All four 2-GPU 5-step preflights completed with finite train and fixed-val loss. No OOM, SIGFPE, NaN/Inf, or decode failures occurred after the dataset preparation fix.

A/B camera-only all-block scopes are substantially slower than C/D limited-block scopes. The sweep remains valid but will be long-running; it must stay in tmux and be monitored. The trainer scheduler was fixed to step only on true optimizer steps before launching the 200-step sweep.
