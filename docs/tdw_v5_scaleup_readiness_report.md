# TDW v5 Scale-Up Readiness Report

Date: 2026-06-10

## Result

TDW scale-up was not run.

Reason:

- TDW/Unity generation depends on an Xorg `DISPLAY`, not only `CUDA_VISIBLE_DEVICES`.
- Previous audits only confirmed GPU0-bound `DISPLAY=:8`.
- This request allowed GPU4-7 for PyTorch warmup/rollout/reward tasks, but did not approve GPU0 for TDW.
- No confirmed GPU4-7 TDW display is available in the current project state.

## Is Scale-Up Required Before Next Gate?

No for the immediate next gate.

The v5 200 dataset is enough for a small camera-conditioned warmup and rollout inspection gate. Scaling to 1k is useful later, but should follow rollout/reward sanity checks so we do not generate a large dataset against an unverified model response.

## Recommended Action

Proceed with existing v5 200 for warmup/rollout gates.

For new TDW generation, choose one:

1. Approve GPU0-bound `DISPLAY=:8` for a bounded v5 scale-up.
2. Configure a GPU4-7 TDW Xorg display.
3. Defer scale-up until after base-vs-adapter rollout inspection.
