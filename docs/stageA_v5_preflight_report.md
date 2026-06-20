# StageA v5 Preflight Report

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


## Fixed-Val Preflight Update (2026-06-20 19:25 CST)

- The first formal StageA launch was stopped at low branch step 102 after audit found that `val_every_optimizer_steps` was configured but no fixed validation forward-loss path was implemented.
- StageA training was stopped only by terminating the StageA tmux sessions/processes. TDW tmux sessions `tdw_v5_4000_gpu0_scaleup` and `tdw_v5_4000_monitor` remained alive and were not attached, killed, or modified.
- Implemented fixed validation forward-loss in `src/physical_consistency/stages/stage1_physinone_cam/trainer.py`:
  - fixed `metadata_val.csv` subset;
  - center temporal window;
  - deterministic validation noise;
  - deterministic branch-specific timestep bins;
  - distributed reduction across ranks;
  - `fixed_val_metrics.jsonl` and `fixed_val_metrics.csv`;
  - loss gate reason `fixed_val_missing` / `fixed_val_nonfinite` / `fixed_val_three_worse_than_best_10pct`.
- Tests after patch: `compileall` passed, `pytest -q` passed (`8 passed`).
- 2-step single-GPU fixed-val smoke passed on physical GPU7: fixed-val step 1 loss 0.031709, step 2 loss 0.031401, both finite.
- 20-step single-GPU preflight passed on physical GPU7:
  - steps: 20/20;
  - fixed-val step 10: weighted 0.045526, unweighted 0.155262, finite;
  - fixed-val step 20: weighted 0.045384, unweighted 0.155166, finite;
  - final train loss: 0.042050;
  - EMA20: 0.047638;
  - EMA100: 0.061135;
  - gradient clipping: 0 triggered in inspected rows;
  - camera/self/cross/ffn LoRA gradients all nonzero;
  - checkpoint files were adapter/training state only; no full model `.bin` or `.safetensors` files were found in the preflight output.
- Result: preflight PASS. Formal StageA may be restarted only with the fixed-val trainer.

<!-- STAGEA_V5_DATAFIX_TRAIN_20260621_START -->
## 2026-06-21 StageA v5 datafix / broad-LoRA status

Status: **RUNNING_NOT_FINAL**. The formal StageA broad-LoRA warmup has been launched and is being monitored, but low/high branches have not completed yet.

Current H20 state at `2026-06-21T02:13:20+08:00`:

- Repo branch: `research/stageA-v5-datafix-train-20260620`
- Current code commit before this documentation update: `15e070448581a6519a7482432d6bebf5c4da471f`
- Formal training tmux: `stageA_v5_broad_lora_train_20260621_0125` (`alive=yes`)
- Monitor tmux: `stageA_v5_broad_lora_monitor_20260621_0205` (`alive=yes`)
- Monitor log: `local_assets/experiments/exp_stageA_v5_datafix_train_gate/formal_stageA_schedulerfix_gradaccum1_snapshot_20260620_144547/logs/monitor_20260621_0205.log`
- Formal output root: `local_assets/experiments/exp_stageA_v5_datafix_train_gate/formal_stageA_schedulerfix_gradaccum1_snapshot_20260620_144547`
- TDW tmux sessions preserved and not touched:

```text
tdw_v5_4000_gpu0_scaleup: 1 windows (created Wed Jun 17 13:35:09 2026)
tdw_v5_4000_monitor: 1 windows (created Wed Jun 17 14:44:35 2026)
```

Data gate status:

- Root cause fixed: the old `Validation ok count: 0` conflated raw HDF5 validation with Stage1-ready converted validation, creating a circular dependency.
- New per-sample states: `raw_hdf5_valid`, `conversion_candidate`, `converted_valid`, `stage1_ready`, and `blocked_reason`.
- Immutable snapshot: `snapshot_20260620_144547`.
- Snapshot is a **partial generated_v5 snapshot**, not the full 4000/5000 dataset.
- Stage1-ready count: 368 samples.
- Split: train 312 / val 36 / test_holdout 20.
- Distribution: mostly `drop` (360) plus early `collision` (8); this is suitable for running infrastructure validation and formal StageA start, but not a complete balanced v5 corpus.

Preflight status:

- Single formal-config preflight passed with `CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7`, `nproc_per_node=7`, `gradient_accumulation_steps=1`, full 81-frame clips, and diagnostic stop at 20 optimizer steps.
- Loss and gradients were finite.
- All four broad-LoRA groups had nonzero gradients: camera conditioning, self-attention, cross-attention, and FFN.
- Base model, VAE, and T5 remained frozen.
- Physical GPU0 was not used for training.

Formal StageA run status:

- Source model: LingBot-Fast camera model at `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`.
- Physical GPUs used for training: GPU1-7 only via `CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7`.
- Branch mode: `sequence`.
- Current branch: `low`.
- Low branch schedule: min 800 / target 1200 / hard max 1600 optimizer steps.
- High branch schedule: min 1000 / target 1600 / hard max 2200 optimizer steps.
- Scheduler: linear warmup + cosine decay, raw scheduler kept outside `accelerator.prepare`, one scheduler step per optimizer step.
- Latest observed metrics rows: 29.
- Latest observed optimizer step: 29.0.
- Latest observed loss: 0.03999931365251541.
- Latest observed EMA20 / EMA100: 0.03751984179410186 / 0.027830362918671702.
- Latest observed LR: 1.8750000000000003e-06.
- Latest observed gate: WAIT (below_min_steps;spike_ratio_high).
- Latest observed GPU reserved memory per rank was stable around 84 GiB in the early run.
- No StageB, DPO, reward scoring, rollout, or pair mining has been run.

Interpretation:

The run is now past model-loading and early optimizer-step smoke. It is training for real on GPU1-7, with metrics and monitor logs being written. It must remain `RUNNING_NOT_FINAL` until the low and high branches finish and the normal-loss gate evaluates the required minimum/target steps.
<!-- STAGEA_V5_DATAFIX_TRAIN_20260621_END -->
