# DPO Engineering Run-through v2 Report

Current Status: PASS_ENGINEERING_ONLY / LEARNING_NOT_CLAIMED
Updated: 2026-06-29 14:18:28

## Scope

This run-through used V2V-5 prefix conditioning and future-only DPO energy. It was intentionally tiny: no StageB, no GRPO, no full-data StageA, and no large-scale DPO. The goal was to verify the training/evaluation chain, checkpoint saving, true V2V-5 video generation, and metric plumbing.

## Input

- Pair manifest: `manifests/dpo_engineering_runthrough_v2_8.jsonl`
- Pair type: 8 Type A local-corruption pairs, because Protocol v2 rejected Type B rollout losers for blur/sharpness quality.
- Objective: SDPO-style winner-preserving run-through with explicit winner anchor (`sdpo_anchor`).
- LoRA: camera-conditioning only, rank 4.
- Trainable params: 6553600
- LoRA modules: 160 total, groups={'camera_conditioning': 160}
- GPU: CUDA_VISIBLE_DEVICES=7

## Runtime Result

- Runtime status: `PASS`
- Optimizer steps: 10
- Checkpoints: step0, step5, step10
- Finite loss: True
- Nonzero grad: True
- Save/load OK: True
- Final objective loss: 0.7151395082473755
- Final DPO loss: 0.693133533000946
- Final implicit accuracy: 1.0
- Final winner improvement: -0.00038708746433258057
- Final loser degradation: 0.0006595700979232788
- Final winner contribution ratio: 0.0

Engineering pass means the chain runs. It does not mean the DPO objective is learning useful preferences. Winner improvement is negative and winner contribution ratio is 0, so the learning signal is still loser-dominant.

## Checkpoint Video Eval

Each checkpoint generated one real V2V-5 sample using prefix frames 0-4 and future frames 5-80. Contact sheets were manually inspected by Codex.

| checkpoint | PSNR | SSIM | sharpness | visual conclusion |
|---|---:|---:|---:|---|
| step000 | 14.1284 | 0.8418 | 31.9857 | generated future has background drift and foreground hallucination; not visually improved |
| step005 | 15.0270 | 0.8727 | 32.9768 | generated future has background drift and foreground hallucination; not visually improved |
| step010 | 14.5785 | 0.8673 | 31.1569 | generated future has background drift and foreground hallucination; not visually improved |

LPIPS backend is available. FVD remains `BLOCKED_BY_ENV` because a real video FVD backend is not installed. VBench remains `BLOCKED_BY_ENV` because `vbench` is not installed and large model downloads were not started.

## Decision

DPO engineering is ready for future tiny experiments, but DPO training should not scale yet. The next learning experiment should keep the engineering checks but alter the objective or LoRA capacity: winner-anchor stronger than this run, high-noise-aware sampling, and possibly limited temporal/self-attention LoRA rather than camera-only rank4.
