# Fast BF16 SIGFPE Investigation

Status: in_progress_not_final

Date: 2026-06-22

## Scope

This investigation is for the corrected LingBot-World-Fast StageA high-noise-only path. It must not be used to justify falling back to LingBot-Base, full FP32 training, StageB, DPO, reward scoring, or rollout.

## Current Result

A basic BF16 kernel diagnostic was run on physical GPU7 via `CUDA_VISIBLE_DEVICES=7`.

Passed checks:

- BF16 tensor allocation
- BF16 GEMM
- BF16 LayerNorm
- BF16 PyTorch SDPA
- finite outputs
- no SIGFPE
- no NaN/Inf

Output files:

- `reports/fast_bf16_sigfpe_matrix.csv`
- `reports/fast_stageA/fast_bf16_env_report.json`

Observed peak memory for the basic diagnostic was about 37 MB. This only proves the basic runtime/kernel path is sane. It does not yet prove LingBot-Fast model forward/backward or DDP safety.

## Next Required Checks

Before formal Fast StageA training:

1. Fast model BF16 load smoke.
2. Fast single-GPU 20-step high-only forward/backward/optimizer preflight.
3. Fast 2-GPU DDP 20-step preflight.
4. Fast 7-GPU DDP 20-step preflight.
5. Fixed validation with checkpoint-invariant noise.
6. Adapter save/load round trip.

## Current Guardrails

- `scripts/debug_fast_bf16_sigfpe.sh` refuses `CUDA_VISIBLE_DEVICES=0`.
- `scripts/launch_fast_stageA_high_only.sh` refuses `CUDA_VISIBLE_DEVICES=0`.
- Basic GPU0 guard check returned exit code 2 before model import.

## Interpretation

If SIGFPE reappears in later Fast preflight, the likely root is not the most basic BF16 GEMM/LayerNorm/SDPA runtime. The next suspects are Fast model shape assumptions, attention backend choice, camera-control tensor numerics, LoRA autocast/chunking, or DDP/rank divisibility.
