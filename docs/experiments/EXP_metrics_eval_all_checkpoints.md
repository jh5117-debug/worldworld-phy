# EXP Metrics Eval All Checkpoints

Status: in_progress

## Question

Which available LingBot-Fast adapter checkpoint is actually best for DPO candidate generation when judged by real rollout videos, traditional video metrics, PhysGeo diagnostics, and Codex visual audit?

## Models

- M0: Original LingBot-Fast
- M1: previous camera-only tiny LoRA, only if strict metadata can be reconstructed safely
- M2/M3: broad-LoRA step800/final883, only if available and strict Fast adapter loading succeeds
- M4-M7: small-LoRA A/B/C/D checkpoints
- M8: selected candidate from screen16 selection, currently `D_step050`

## Benchmark

- Primary: `manifests/quant_benchmark_v1_all.jsonl`
- Quick screen: `manifests/small_lora_screen16.jsonl`
- Frame count: 81
- Resolution: 480x832
- use_action: false
- Conditions must use identical image/prompt/poses/intrinsics/seed/scheduler settings across models.

## Metrics

Traditional:

- PSNR
- SSIM
- LPIPS
- FVD
- VBench, if the official environment is available

PhysGeo:

- BRC / CAF proxies where implemented
- Epipolar Sampson diagnostics
- C-SGC diagnostics
- Freeze / blur / flicker / quality proxies

Unavailable metrics must be reported as missing or blocked, not faked.

## Visual Audit

Every generated video must receive a contact sheet and structured Codex audit row.

## Success Gate

The chosen model cannot be selected by loss alone. It must avoid broad visual collapse, foreground identity regression, freeze cheating, and severe camera ignoring.

## Output

- `local_assets/eval_metrics_<timestamp>/`
- `reports/eval_metrics_<timestamp>/`
- `reports/video_audit/eval_metrics_<timestamp>/`
- `docs/eval_metrics_full_report.md`
- `docs/model_weight_video_eval_decision.md`



## Current Status Update (2026-06-27 01:28:06)

- screen16 artifacts are available.
- full80 all-checkpoint rollout is incomplete; current full80 covers `GT, original_fast, D_step050` only.
- prefix-aware conditioning code and tests are implemented.
- diagnostic DPO preflight status: `PASS`.
- LingBot-Fast DPO backend status: `BLOCKED_FAST_ENERGY_BACKEND`.
- DPO probe remains blocked until real winner/loser energy is callable.
