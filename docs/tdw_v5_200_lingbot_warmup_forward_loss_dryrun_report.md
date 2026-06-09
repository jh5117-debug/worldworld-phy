# TDW v5 200 LingBot Warmup Forward-Loss Dry-Run Report

Date: 2026-06-09

## Scope

Command used the no-training flags:

- `--no_backward true`
- `--no_optimizer true`
- `--no_checkpoint true`
- `--use_action false`

GPU policy:

- GPU0 was not used.
- First attempt with `CUDA_VISIBLE_DEVICES=6,7` blocked because GPU6 was busy.
- User later clarified GPU4-7 may be used and existing jobs may be killed, but the original GPU4-7 job was root-owned and current SSH user lacked passwordless sudo, so it could not be killed directly.
- A second dry-run used `CUDA_VISIBLE_DEVICES=7` after GPU7 was free.

## Result

- Status: `passed_placeholder_no_model_load`
- CUDA visible devices: `7`
- Latent placeholder shape: `[1, 4, 8, 60, 104]`
- Camera placeholder shape: `[1, 8, 4, 4]`
- Loss value: `0.0`
- Loss finite: yes
- No backward: confirmed
- No optimizer: confirmed
- No checkpoint: confirmed

## Important Limitation

This was not a full LingBot-Fast/VAE/T5 model-load forward. The safety script intentionally verified the no-backward/no-optimizer tensor path only. A real model-load forward-loss smoke remains required before any warmup pilot can be considered technically passed.

## Recommendation

Do not start warmup training yet. The next approved step should be a real LingBot-Fast model-load forward-loss smoke on a free GPU7 or GPU6/7 window, still with no backward, no optimizer, and no checkpoint.
