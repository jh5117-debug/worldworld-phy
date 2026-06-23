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

## 2026-06-23 Update: Micro and True-Model BF16 LoRA Preflights

Status: true-model BF16 LoRA preflight passed after formal StageA completed.

Micro preflight:

- Path: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/bf16_sigfpe_micro_preflight_20260623_013813/`
- Physical GPU: GPU6 via `CUDA_VISIBLE_DEVICES=6`.
- Result: 9/9 cases passed.
- Covered BF16 GEMM backward, LayerNorm/MLP backward, SDPA native backward, SDPA math fallback backward, non-reentrant checkpoint backward, full-replay checkpoint backward, LoRA BF16 autocast, LoRA BF16 no-autocast, and current safe LoRA FP32 no-autocast.
- No SIGFPE, NaN/Inf, or OOM was observed.

True-model preflight:

- Path: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/true_model_bf16_lora_preflight_after_formal_20260623_014055/`
- Physical GPU: GPU7 via `CUDA_VISIBLE_DEVICES=7`.
- Model: LingBot-World-Fast.
- Settings: `PC_FORCE_LORA_FP32=0`, `PC_LORA_DISABLE_AUTOCAST=0`.
- LoRA dtype: `bfloat16`.
- Matched LoRA layers: 560 total, with camera conditioning 160, self-attention 160, cross-attention 160, FFN 80.
- Diagnostic optimizer steps: 2/2 completed.
- Fixed-val at step 2: 0.109535 weighted / 0.174363 unweighted, finite.
- Exit status: 0.

Interpretation:

The current H20 PyTorch/CUDA runtime can run both small BF16 component tests and a true LingBot-World-Fast BF16-LoRA diagnostic without reproducing SIGFPE. The formal completed StageA run still used the conservative mixed-safe LoRA FP32 path. A future speed-focused run may consider BF16 LoRA/autocast, but it should be treated as a new run configuration rather than a mid-run change.
