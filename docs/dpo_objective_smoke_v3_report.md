# DPO Objective Smoke v3 Report

Current Status: ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL
Updated: 2026-06-30 05:14:29

## Scope

Ran the gated `DPO_smoke_v3_8` engineering smoke on `manifests/dpo_objective_smoke_v3_8.jsonl` after Protocol v3 produced 34 TypeA-only pairs and LocalDPO spatial mask v2 passed. This was a tiny engineering run-through, not scale DPO.

## Training Smoke

- Objective: SDPO-anchor v3 diagnostic (`L_safe_dpo + lambda_w * E_policy_winner`).
- Pair count: 8 TypeA local-corruption pairs.
- Steps: 10.
- LoRA scope: camera-conditioning only, rank 4, 160 modules, 6,553,600 trainable params.
- Runtime checks: nonzero grad = True; save/load = True; same noise = True; same timestep = True.
- Final DPO loss: 0.693122; final objective loss: 0.697414.
- Mean winner improvement: 9.940029e-06; final winner improvement: 2.165623e-04.
- Mean loser degradation: 1.058423e-04; final loser degradation: 2.856739e-04.
- Mean winner contribution ratio: 0.352; final winner contribution ratio: 0.431.

Decision: engineering chain is runnable, but objective signal is still weak / unstable and should not be scaled.

## Checkpoint Video Smoke

True V2V-5 checkpoint video smoke was run for step000, step005, and step010 on one screen16 sample each. This is a checkpoint-load and video-generation smoke, not full screen16 evaluation.

| checkpoint | PSNR | SSIM | LPIPS | sharpness | FVD | VBench |
|---|---:|---:|---:|---:|---|---|
| step000 | 16.4658 | 0.8786 | 0.6611 | 63.02 | BLOCKED_BY_ENV | BLOCKED_BY_ENV |
| step005 | 16.3919 | 0.8779 | 0.6606 | 56.33 | BLOCKED_BY_ENV | BLOCKED_BY_ENV |
| step010 | 16.3143 | 0.8772 | 0.6535 | 54.32 | BLOCKED_BY_ENV | BLOCKED_BY_ENV |


Codex visual audit: all three checkpoint contact sheets are readable but show no visual improvement. The generated future remains darker than GT and exhibits hallucinated green fragments / foreground duplicates and object identity instability. No black screen or global freeze was observed in this one-sample smoke.

## Metric Backend Notes

- PSNR / SSIM / LPIPS: PASS on checkpoint video smoke.
- FVD: BLOCKED_BY_ENV because no real local video FVD backend with temporal feature weights is available; image FID was not substituted.
- VBench: BLOCKED_BY_ENV because the `vbench` package/evaluator is not installed locally; large model downloads were not started automatically.

## Decision

`DPO_smoke_v3` is ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL. It proves the tiny SDPO-anchor chain can run, save/load checkpoints, and generate true prefix5 V2V-5 videos, but it does not provide evidence to scale DPO. Next work should fix objective signal and TypeB data quality before any larger DPO.

Explicitly not run: StageB, GRPO, full-data long StageA, or large-scale DPO. No checkpoint/data/weight deletion was performed.
