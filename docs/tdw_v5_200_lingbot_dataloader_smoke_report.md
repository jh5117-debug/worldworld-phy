# TDW v5 200 LingBot Dataloader Smoke Report

Date: 2026-06-09

Status: passed.

The smoke was rerun on the H20 helper worktree before the true forward-loss gate.

## Manifests

| Split | Count |
|---|---:|
| train | 160 |
| val | 20 |
| test | 20 |

## Batch Shapes

Checked one batch per split with `batch_size=2`, `num_frames=81`, resolution `480x832`.

| Tensor | Shape |
|---|---|
| image | `[2, 480, 832, 3]` |
| video | `[2, 81, 480, 832, 3]` |
| poses | `[2, 81, 4, 4]` |
| intrinsics | `[2, 81, 4, 4]` |
| action | `[2, 81, 4]` |

## Checks

- target.mp4 decode: passed for sampled train/val/test batches.
- metadata `use_action=false`: passed.
- dummy action norm: `0.0`.
- prompt: non-empty.
- camera condition files: present and readable.
- failures: none.

Ready for true model forward smoke: yes.

Raw report path:

`local_assets/experiments/exp_tdw_v5_200_true_forward_loss_gate/dataloader_smoke/dataloader_smoke_report.json`
