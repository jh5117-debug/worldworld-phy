# StageA v5 Runbook

# StageA v5 datafix/train gate status (2026-06-20)

- Branch: `research/stageA-v5-datafix-train-20260620`.
- Baseline: `cf0ebc3954d0fd7b3bec98a9c5232db7139a4f06`.
- Scope: generated_v5 raw validation -> conversion validation -> Stage1-ready immutable snapshot -> broad-LoRA StageA warmup.
- Safety: GPU0/DISPLAY=:8 TDW tmux sessions were preserved; StageA uses only GPU1-7. StageB, DPO, reward, rollout, and pair mining were not run in this fix commit.

## Validation root cause

The old report showed `Validation ok count: 0` because the validation gate conflated raw simulator HDF5 validity with converted Stage1-ready files. Raw generated_v5 samples naturally do not contain `target.mp4`, `poses.npy`, or `intrinsics.npy` until conversion, so requiring those files during raw validation created a circular dependency: conversion required validation, while validation required conversion.

The fix separates per-sample states:

- `raw_hdf5_valid`: HDF5 opens, chunk is complete/inactive, frame keys and RGB/depth/id/camera/object state metadata are valid and finite.
- `conversion_candidate`: raw sample is safe to convert.
- `converted_valid`: Stage1 files exist and decode, with 81 frames at 16 fps, finite `poses.npy`, finite `[fx, fy, cx, cy]` intrinsics, non-empty prompt, `control_type=cam`, and `use_action=false`.
- `stage1_ready`: both raw and converted gates pass.
- `blocked_reason`: explicit per-sample reasons when any gate fails.

The snapshot builder now reads per-sample validation JSONL and rejects duplicate or mismatched sample ids; it no longer promotes an entire chunk based on aggregate chunk counts.

## Immutable snapshot

- Snapshot timestamp: `20260620_144547`.
- Validation JSONL: `local_assets/experiments/exp_stageA_v5_datafix_train_gate/validation/snapshot_20260620_144547/stageA_v5_validation.jsonl`.
- Snapshot manifests: `local_assets/experiments/exp_stageA_v5_datafix_train_gate/manifests/snapshot_20260620_144547/`.
- Stage1 dataset directory: `local_assets/experiments/exp_stageA_v5_datafix_train_gate/stage1_dataset_snapshot_20260620_144547/`.
- Eligible/stage1-ready samples: 368/368.
- Split: train 312 / val 36 / test_holdout 20.
- SHA256: all `71e2323fc00588a93fff253a1fc8eb7634cc4be96c704038beff6bde534ba486`; train `9f79a2edc4bbbf89dbecf763f24136faf609e259e15aef4cd12e054edf3725fd`; val `cb8d95fb5dbe1a3e22057212e92380dce78805cd5fee4f93963d75621b574341`; test `d8bb5cda35c84f883e69050b40c51aad3c1d7eeebdabdd13f9510d19153dd8a1`; validation `6c30fdc9181b1b4e5ee92af444cd99b97e764117a79274a68f942d28d909844f`.
- This is a **partial generated_v5 snapshot**, not the full 4000/5000 dataset. Current converted coverage is mostly `drop` with a small `collision` tail: drop 360 / collision 8.

## StageA config/preflight

- Temporal length: 81 frames at 480x832. The 8-frame setting is only smoke and is not used for formal StageA.
- LoRA scope: broad LoRA over camera conditioning, self-attention, cross-attention, and FFN linear layers.
- LoRA config: rank 16, alpha 16, dropout 0.05, all blocks, out-of-place merge mode.
- Trainable params in preflight: 102,891,520 LoRA params across 560 linears; base DiT, VAE, T5/text encoder, norms, patch embedding, and output head remain frozen.
- Branch schedule: low min/target/hard 800/1200/1600 optimizer steps; high min/target/hard 1000/1600/2200 optimizer steps.
- Optimizer/scheduler: AdamW, lr 5e-6, eta_min 5e-7, betas [0.9, 0.95], weight_decay 0.01, 5% LR warmup, cosine decay, max grad norm 1.0, bf16 mixed-safe.
- Loss monitoring logs `metrics.jsonl`, `metrics.csv`, EMA20/EMA100, lr, timestep/sigma, grad norms before/after clipping, LoRA group grad norms, LoRA parameter/update norms, step time, and GPU memory.
- Single-card preflight on GPU7 with snapshot `20260620_144547` completed 2/2 optimizer steps: loss 0.056813 -> 0.078419, finite gradients, gate PASS, adapter-only checkpoint saved, GPU7 released.

## Adapter-only checkpoint policy

The trainer no longer writes full model weights. Branch checkpoints contain adapter LoRA tensors plus training state for resume. The sequence runner now creates `stage1_final_adapter_bundle` with low/high adapter symlinks and an adapter manifest instead of materializing a full eval checkpoint bundle.

## Formal launch policy

Use `CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7` only if those physical GPUs are free. Never include GPU0. Launch with `branch_mode=sequence`; low runs before high. Keep TDW tmux sessions untouched.
