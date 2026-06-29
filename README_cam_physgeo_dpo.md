# Cam PhysGeo DPO Current Status

## Current Protocol v3 Status (2026-06-29 15:38:49)

- Metrics backend v2: PSNR/SSIM/LPIPS PASS; FVD/VBench BLOCKED_BY_ENV with attempted fixes recorded.
- LocalDPO spatial mask v2: PASS, 34/34 Type A pairs have usable spatial+time masks.
- Protocol v3: 34 valid Type A pairs, 0 Type B, 0 Type C.
- Candidate generator v2: waiting for GPU capacity; current GPUs are occupied by unrelated workloads.
- DPO smoke v3: not run yet because GPU capacity is unavailable; no scale DPO.



## Current DPO Protocol v2 Status (2026-06-29 14:18:28)

- Protocol v2 manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Valid v2 pairs: 34 total, 34 Type A, 0 Type B, 0 Type C.
- Type B rollout losers are currently blocked by blur/sharpness gates; do not use them for DPO.
- Metrics backend: PSNR/SSIM/LPIPS pass; FVD and VBench are BLOCKED_BY_ENV.
- DPO engineering run-through: PASS_ENGINEERING_ONLY on 8 Type A pairs for 10 steps with checkpoint video eval. Learning signal remains loser-dominant, so do not scale DPO.
- Explicitly not run: StageB, GRPO, full-data long StageA, large-scale DPO.


Updated: 2026-06-28T00:20:04

## Preference Pair Protocol v1

DPO training remains paused. The current work produced a stable V2V-5 preference-pair protocol:

- `manifests/dpo_preference_protocol_v1_pairs.jsonl`
- 66 valid pairs
- Type A local corruption: 50
- Type B medium-hard rollout loser: 16

Recommended next DPO input: start with Type A after full real-energy audit, then cautiously mix Type B.

---

# Cam PhysGeo DPO Current Status

Updated: 2026-06-27T17:40:45

## Current Result

The project now has a real prefix-aware V2V-5 path through StageA warmup, inference, visual audit, metric scoring, and a tiny LingBot-Fast energy-form DPO probe.

- Pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Prefix condition: frames 0-4
- Prediction/evaluation target: frames 5-80
- StageA V2V-5 final: `STAGEA_V2V5_MIXED_USE_WITH_CAUTION`
- DPO BF16 backend: `DPO_BF16_READY`
- Tiny DPO probe: `DPO_PROBE_FAILED` for scale-up

Reason for DPO failure: the backend runs, but loss stays near 0.693, winner improvement is too small/negative at the end, and DPO step20 video quality is not better than Original Fast or StageA final. Do not scale DPO from this checkpoint.

---

# Readme Cam Physgeo Dpo

Updated: 2026-06-27T07:14:17

## Current DPO Prefix5 Status

- Old I2V-1 pair manifest is deprecated.
- New V2V-5 pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`.
- Real LingBot-Fast DPO energy backend is implemented using future-only flow-matching energy.
- DPO BF16 preflight status: **DPO_BF16_READY** (single GPU, DDP2, and DDP8 all PASS).
- Tiny DPO probe is **blocked** pending a verified V2V-5 generation/evaluation wrapper; no probe checkpoint video metrics have been produced yet.

See `docs/dpo_bf16_preflight_report.md` for details.

---

# Cam PhysGeo DPO Current Status (2026-06-27 04:43:25)

Current DPO input is V2V-5, not I2V-1:
- Active pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Prefix frames 0-4 are condition.
- Future frames 5-80 are winner/loser targets.
- Loss/reward are future-only.

The real LingBot-Fast DPO energy backend is implemented for BF16 preflight, but DPO is not yet approved to scale. A tiny probe can only start after single-GPU, DDP2, and DDP8 preflight gates pass.


---

# Cam-PhysGeo DPO Current Status

Updated: 2026-06-27 01:28:38

Current DPO status: BLOCKED for real LingBot-Fast training. The repository now has energy-form anchored DPO loss plus a diagnostic trainer path that validates anchored pairs, same noise/timestep, backward, optimizer step, and save/load. The real policy/reference LingBot-Fast flow-matching energy backend is still required before BF16 DPO preflight or DPO probe can be claimed.

# Current Status Update - 2026-06-24

- New active branch: `research/quant-small-lora-dpo-probe-20260624` from `63d1b93`.
- Broad-LoRA is no longer the main route for candidate generation because generation quality was FAILED_OR_MIXED despite fixed-val loss improvement.
- Current focus: Quantitative Benchmark v1, small/low-rank LoRA scope sweep, Reward Calibration v2, and anchored DPO probe.
- GPU0-7 are authorized for this round; no full-data long StageA, no StageB, no GRPO, and no large-scale DPO.
- DPO data strategy: GT winners plus quality-bounded hard-negative losers selected from Original Fast, last-week camera-only tiny LoRA, small-LoRA sweep candidates, controlled corruptions, and broad-LoRA only if it passes loser quality floor.

---

# Formal Fast High-Only StageA Launch - 2026-06-22 19:43 CST

A balanced partial generated_v5 snapshot is now active for formal StageA. It contains 400 Stage1-ready samples, with 100 each for drop, collision, roll, and containment. Clean validation passed 400/400 with `raw_hdf5_valid=true`, `converted_valid=true`, and `stage1_ready=true`; blocked count is 0. The split is train 342 / val 43 / test_holdout 15.

Snapshot paths:

- Validation JSONL: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/validation_balanced_20260622_1830/stageA_v5_validation.jsonl`
- Snapshot manifests: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/manifests/balanced_snapshot_20260622_1830/`
- Stage1 dataset: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/stage1_dataset_balanced_snapshot_20260622_1830/`

Balanced snapshot GPU7 preflight passed on the same 81-frame dataset: 2 optimizer steps, finite loss and fixed validation, Fast model loaded from `lingbot_world_fast`, and broad-LoRA groups hit camera conditioning, self-attention, cross-attention, and FFN.

Formal training session:

- tmux: `fast_stageA_high_only_formal_balanced_20260622_1925`
- branch: `high_only`
- physical GPUs: 1,2,3,4,5,6,7
- GPU0: not used for training; TDW/Xorg only
- optimizer plan: min 400 / target 800 / hard max 1200
- latest observed step: 3/800 at 2026-06-22 19:43 CST
- observed losses: 0.207341 -> 0.133926 -> 0.113493
- gate state: WAIT only because below minimum steps
- gradients: finite; all four LoRA groups nonzero
- memory: about 83.9 GiB used per physical GPU1-7 during active training

This is still **RUNNING_NOT_FINAL**. Do not mark StageA PASS until the high-only branch reaches the configured loss-normal gate. StageB, DPO, reward, rollout, and pair mining remain not run.

# Current Project Status - 2026-06-22 17:18 CST

The active StageA route is now **LingBot-World-Fast high-only**. The previous Base low->high run is retained only as invalid history and must not be used as StageA evidence, a StageB substitute, or a DPO starting point.

Current status:

- Fast high-only code path: implemented.
- Fast high-only preflights: passed on GPU7, GPU6/7, and GPU1-7.
- Formal StageA: waiting for balanced generated_v5 converted snapshot.
- Latest converted distribution: 868 Stage1-ready samples; drop 816, containment 18, collision 17, roll 17.
- TDW generation continues on GPU0/DISPLAY=:8 and must not be interrupted.
- GPU1-7 are reserved for future StageA high-only training after the data gate passes.
- StageB, DPO, reward scoring, rollout, and pair mining have not been run.

# Cam-PhysGeo-DPO

Camera-Conditioned Physical-Geometric Preference Alignment for LingBot-Fast / LingBot-Base.

Build a dry-run manifest:

```bash
python -m cam_physgeo.data.build_manifest   --phyinone_root /home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam   --movingcam_root /home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets   --out manifests/cam_physgeo_all.jsonl   --dry-run --limit 50
```

Convert cam-only inputs:

```bash
python -m cam_physgeo.data.convert_to_lingbot_cam_inputs   --manifest manifests/cam_physgeo_train.jsonl   --out data/cam_physgeo_lingbot_inputs/train   --num_frames 81 --fps 16 --size 480x832   --use_action false --make_dummy_action true --dry-run
```

Run reward calibration skeleton:

```bash
bash scripts/04_reward_calibration.sh --dry-run --limit 20
```

No deletion, long training, model download, or checkpoint mutation is part of this first stage.

## StageA v5 datafix/train gate update - 2026-06-20

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

<!-- STAGEA_V5_AUDIT_ETA_20260621_START -->
## 2026-06-21 StageA running audit and ETA

Audit time on H20: `2026-06-21T06:47:57+08:00`.

Current status:

- Branch: `research/stageA-v5-datafix-train-20260620`
- HEAD before this ETA doc update: `70bbf72ac85c11723aef87e302c21bfd6fedf235`
- Formal training tmux: `stageA_v5_broad_lora_train_20260621_0125` (`alive=yes`)
- Monitor tmux: `stageA_v5_broad_lora_monitor_20260621_0205` (`alive=yes`)
- StageA branch currently running: `low`
- Current optimizer step: 253 / low target 1200 / low hard max 1600
- Latest train loss: 0.019976750016212463
- Latest EMA20 / EMA100: 0.04283223633413844 / 0.046242957450449304
- Latest LR: 4.857693325650949e-06
- Latest gate state: `WAIT` with reasons `below_min_steps;spike_ratio_high`
- Latest fixed-val step: 200.0
- Latest fixed-val weighted loss / best: 0.04660887425499303 / 0.04660887425499303
- Fixed-val finite: 1.0
- TDW generated_v5 raw HDF5 count at audit: 2524
- TDW tmux sessions preserved:

```text
tdw_v5_4000_gpu0_scaleup: 1 windows (created Wed Jun 17 13:35:09 2026)
tdw_v5_4000_monitor: 1 windows (created Wed Jun 17 14:44:35 2026)
```

GPU isolation:

```text
0, 28 MiB, 97871 MiB, 0 %
1, 85688 MiB, 97871 MiB, 100 %
2, 85688 MiB, 97871 MiB, 100 %
3, 85688 MiB, 97871 MiB, 100 %
4, 85688 MiB, 97871 MiB, 100 %
5, 85688 MiB, 97871 MiB, 100 %
6, 85688 MiB, 97871 MiB, 100 %
7, 85688 MiB, 97871 MiB, 100 %
```

Observed timing:

- Empirical training speed after early warmup: ~73.5 seconds / optimizer step.
- Low branch remaining to target: ~19.3 hours.
- Low branch remaining to hard max if gate does not pass: ~27.5 hours.
- High branch target duration after low completes: ~32.6 hours.
- High branch hard-max duration if needed: ~44.9 hours.
- Approximate time to complete low target + high target: ~52.0 hours from this audit.
- Conservative low hard + high hard upper bound: ~72.4 hours from this audit.

Interpretation:

The run is healthy and still early relative to the formal loss gate. The `WAIT` state is expected because the low branch has not reached its minimum 800 optimizer steps. `spike_ratio_high` is being tracked as a gate reason, but fixed validation is finite and improved from step 100 to step 200. No StageB, DPO, reward scoring, rollout, or pair mining has been run.

Current error scan:

```text
none
```
<!-- STAGEA_V5_AUDIT_ETA_20260621_END -->

## 2026-06-22 Fast StageA Direction

The active StageA path has been corrected:

- Use LingBot-World-Fast, not LingBot-Base.
- StageA is high-noise-only for global camera/layout/background structure.
- StageB is future low/mixed-noise foreground/detail refinement and is not part of the current run.
- DPO remains later and was not run.

Fast high-only preflights now pass on single GPU7, DDP GPU6/7, and DDP GPU1-7. Formal StageA is waiting for a balanced generated_v5 converted snapshot; the current converted subset is still drop/orbit_left-only.