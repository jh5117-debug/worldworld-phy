# Fast BF16 Formal Readiness Report

## Status

`BF16_FORMAL_READY`

## Scope

- LingBot-Fast high-only StageA configuration
- 81 frames, 480x832
- broad-LoRA rank16, alpha16, dropout0.05
- 560 LoRA linear layers: camera_conditioning / self_attention / cross_attention / ffn
- VAE FP32
- LoRA BF16 for BF16 runs
- safe SDPA fallback requested
- camera/projection/loss reductions kept in safe precision path by Stage1 policy

## Outputs

- BF16 root: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/bf16_formal_readiness_20260624_012335`
- Matrix CSV: `reports/meeting_eval_20260624_011137/bf16_preflight_matrix.csv`
- Speed CSV: `reports/meeting_eval_20260624_011137/bf16_speed_benchmark.csv`

## Run Matrix

| Run | Steps | Fixed-val | Duration seconds | Status |
|---|---:|---:|---:|---|
| bf16_single_gpu7_20 | 20/20 | 0.100754 | 4045.4 | PASS |
| safe_single_gpu6_8 | 8/8 | 0.100807 | 2575.7 | PASS |
| bf16_ddp2_gpu6_7_20 | 20/20 | 0.100899 | 3079.5 | PASS |
| bf16_ddp7_gpu1_7_20 | 20/20 | 0.094557 | 3236.0 | PASS |

## Interpretation

- BF16 single GPU7 completed 20/20 optimizer steps with finite loss, finite fixed-val, adapter checkpoint output, and no SIGFPE/OOM/NaN.
- BF16 DDP2 on GPU6,7 completed 20/20 optimizer steps with finite fixed-val and no SIGFPE/OOM/NaN.
- BF16 DDP7 on GPU1-7 completed 20/20 optimizer steps with finite fixed-val and no SIGFPE/OOM/NaN.
- The short safe LoRA-FP32/autocast-disabled run completed 8/8 and provides a conservative comparison baseline, but it is not the required formal BF16 readiness condition.
- DDP logs emit a PyTorch NCCL process-group shutdown warning at exit; the run still completed and released GPUs. This should be cleaned up later, but it did not block readiness.

## Next Use

Next formal StageA high-only training may use BF16 mixed-safe mode on GPU1-7, provided the same safeguards remain active and GPU0 remains excluded.
