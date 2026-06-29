# Implementation Status

## Current Protocol v3 / DPO Smoke Status (2026-06-30 05:14:29)

- Candidate generator v2: CANDIDATE_GENERATOR_FAILED_TYPEB_STILL_BLOCKED; audited 208 existing true V2V-5 small-LoRA rollout candidates, selected 0 usable TypeB rollout losers.
- Protocol v3: MIXED_TYPEA_READY_TYPEB_FAILED_CANDIDATE_GENERATOR; 34 valid TypeA local-corruption pairs, 0 TypeB, 0 TypeC.
- LocalDPO spatial mask v2: PASS; 34/34 TypeA pairs have usable spatial+time masks.
- DPO smoke v3: ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL on 8 TypeA pairs for 10 steps. Runtime/save-load/nonzero-grad checks passed, but winner improvement remains weak/unstable and checkpoint video smoke shows no visual improvement.
- Checkpoint video smoke: step000/005/010 generated true prefix5 V2V-5 videos on 1 screen16 sample each; PSNR/SSIM/LPIPS PASS; FVD/VBench remain BLOCKED_BY_ENV.
- Decision: do not scale DPO. Do not use TypeB rollout losers until blur/sharpness quality is fixed.



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


<!-- DPO_FAILURE_DIAG_20260629_START -->
## Current Status: DPO Failure Root-Cause Diagnosis Completed (2026-06-29)

- S0_sanity_8 objective ablation failed the signal gate, so S1/S2 were not launched.
- Winner-only overfit on the strongest Type B pair did not robustly improve winner energy relative to the reference: mean winner improvement = -2.27876e-05, final = -4.29377e-05.
- Loser-only maximization was weak/non-monotonic: mean loser degradation = 1.04467e-04, final = -1.55047e-04.
- Gradient decomposition found mixed winner/loser alignment: mean cosine(g_w,g_l) = 0.065 and winner/loser grad norm ratio ranged from 0.417 to 10.228.
- Timestep/sigma sensitivity is currently blocked for low/mid bins because all requested bins map to actual sigma about 0.947 in the DPO backend.
- Beta/utility analysis shows `u = Delta_policy - Delta_ref` is effectively zero at initialization, so standard sigmoid DPO starts at the no-margin 0.693 point.
- LocalDPO metadata contains affected spatial masks for 34 / 34 local-corruption pairs, but the current LocalDPO objective only used affected-time masking; spatial-token masking remains TODO.
- Decision: do not proceed with standard DPO or scale DPO. Next probe should use an explicit winner-anchor objective plus conservative loser lambda, and only after spatial LocalDPO masks / sigma sampling are fixed.
- Report: `docs/dpo_failure_root_cause_report.md`.

Safety: no large DPO, no StageB, no GRPO, no full-data StageA, no checkpoint deletion, and no data/weight/video push.
<!-- DPO_FAILURE_DIAG_20260629_END -->


<!-- ENERGY_AUDIT_20260628_START -->
## Current Status: Full Real-Energy Audit Completed (2026-06-28)

- Protocol v1 pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Full real LingBot-Fast energy audit completed for 66 / 66 V2V-5 pairs.
- Real energy outputs: `reports/dpo_preference_protocol_v1/full_real_energy_audit.csv` and `.jsonl`.
- DPO-ready selection: 50 pairs total = 34 Type A local corruption + 16 Type B GT vs medium-hard rollout.
- LocalDPO-ready subset: 34 Type A pairs with affected region/time metadata and positive usable energy margin.
- Type B pairs have stronger real-energy margins (Delta_ref median 0.075306) than Type A local corruptions (Delta_ref median 0.009849), but Type A is better aligned with region-aware LocalDPO.
- Recommendation: tiny standard energy-DPO is unblocked only as a controlled probe; use SDPO-style winner-preserving monitoring and consider Linear-DPO for weak-margin Type A pairs.
- No DPO training, StageB, GRPO, full-data StageA, checkpoint deletion, or data/weight push was run for this audit.

<!-- ENERGY_AUDIT_20260628_END -->

Updated: 2026-06-28T00:20:04

## DPO Preference Protocol v1

- New manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Valid pairs: 66.
- Type A local-corruption pairs: 50.
- Type B GT-vs-medium-hard-rollout pairs: 16.
- No DPO training was run in this protocol pass.
- Decision: protocol ready for review; run full real-energy audit before training.

---

# Implementation Status

Updated: 2026-06-27T17:40:45

## Current V2V-5 / DPO Status

- Active branch: `research/quant-small-lora-dpo-probe-20260624`.
- True prefix-aware V2V-5 generation wrapper is implemented.
- Prefix frames 0-4 are condition; future frames 5-80 are prediction/evaluation target.
- StageA V2V-5 camera-only LoRA warmup completed 100 high-noise steps.
- StageA final decision: `STAGEA_V2V5_MIXED_USE_WITH_CAUTION`.
- Real LingBot-Fast prefix5 DPO energy backend is implemented and BF16-ready.
- Tiny DPO probe completed but failed the scale-up gate: loss stayed near 0.693, winner improvement was tiny/negative at final, and DPO step20 video metrics were below StageA final.
- Current recommendation: do not scale DPO; improve pair quality/reward calibration first.

Safety: no StageB, no GRPO, no full-data long StageA, no large-scale DPO, no checkpoint deletion.

---

# Implementation Status

Updated: 2026-06-27T07:14:17

## Current DPO Prefix5 Status

- Old I2V-1 pair manifest is deprecated.
- New V2V-5 pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`.
- Real LingBot-Fast DPO energy backend is implemented using future-only flow-matching energy.
- DPO BF16 preflight status: **DPO_BF16_READY** (single GPU, DDP2, and DDP8 all PASS).
- Tiny DPO probe is **blocked** pending a verified V2V-5 generation/evaluation wrapper; no probe checkpoint video metrics have been produced yet.

See `docs/dpo_bf16_preflight_report.md` for details.

---

# Implementation Status (2026-06-27 04:43:25)

Latest update:
- Added real prefix5 LingBot-Fast DPO energy backend.
- Added prefix5 DPO dataset loader with asset/schema validation.
- Added strict latent future mask to avoid prefix leakage.
- Wired `train_stage2_anchored_dpo --backend lingbot_fast` to the real preflight runner instead of the previous blocked diagnostic stub.
- Added tests for future mask, backend args, same-noise/timestep, and frozen reference behavior.

Safety status:
- No StageB.
- No GRPO.
- No full-data long StageA.
- No large-scale DPO.
- No checkpoint deletion or historical checkpoint modification.


---

# Current Implementation Status

Updated: 2026-06-27 01:28:38

- Prefix-aware I2V/V2V conditioning code is implemented and tested for prefix_len 1/5/8/16 manifest metadata and latent masks.
- Small-LoRA screen16 sweep artifacts are available; full80 all-checkpoint evaluation is still incomplete.
- Energy-form anchored DPO loss and diagnostic DPO preflight are implemented.
- Real LingBot-Fast anchored DPO remains blocked until a callable winner/loser flow-matching energy backend is exposed.
- LPIPS, FVD, and VBench are blocked in the current environment because the required packages/backends are unavailable.

# Current Status Update - 2026-06-24

- New active branch: `research/quant-small-lora-dpo-probe-20260624` from `63d1b93`.
- Broad-LoRA is no longer the main route for candidate generation because generation quality was FAILED_OR_MIXED despite fixed-val loss improvement.
- Current focus: Quantitative Benchmark v1, small/low-rank LoRA scope sweep, Reward Calibration v2, and anchored DPO probe.
- GPU0-7 are authorized for this round; no full-data long StageA, no StageB, no GRPO, and no large-scale DPO.
- DPO data strategy: GT winners plus quality-bounded hard-negative losers selected from Original Fast, last-week camera-only tiny LoRA, small-LoRA sweep candidates, controlled corruptions, and broad-LoRA only if it passes loser quality floor.

---

# Implementation Status

Completed in first-stage skeleton:

- New branch `cam-physgeo-dpo-refactor`.
- `cam_physgeo` package with data, reward, DPO, TRD, training, eval, and utility modules.
- Configs under `configs/cam_physgeo` with `MOVING_CAM_ROOT`.
- Read-only audit and dry-run scripts.
- Safe delete script written but not executed.
- Storage audit and cleanup manifests written.
- Research and project refocus docs written.

Not yet implemented:

- Real optical-flow/depth/DINO/V-JEPA reward extraction for generated rollouts.
- Real LingBot model loading and training loops.
- Actual corrupted video rendering.
- HDF5 key-level decoder for simulator depth/ID/camera fields.

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

## 2026-06-22 OOM and Low-Gate Fix

Status: mitigation implemented and high-branch resume started.

What failed before:
- Low branch reached 1600 optimizer steps with finite train loss and stable fixed validation, but the old loss gate marked it blocked because spike_ratio_high was treated as a hard failure.
- High branch OOMed during broad-LoRA forward because full 81-frame training used rank-16 broad LoRA with unchunked LoRA inputs and forced FP32 LoRA activations.

Low-gate resolution:
- The gate now separates blocking reasons from advisory reasons.
- spike_ratio_high is advisory when minimum steps are reached, fixed validation is available, and no finite-loss or validation blocker is present.
- Low branch evidence: 1600 optimizer steps, final EMA100 about 0.04387, best fixed-val about 0.04359, final fixed-val about 0.04361. This is stable enough to use as the companion low phase for high-branch resume.

OOM resolution:
- StageA broad-LoRA now uses student_lora_chunk_size=1024.
- The launch script defaults PC_FORCE_LORA_FP32=0 and PC_LORA_DISABLE_AUTOCAST=0, so LoRA activations can run in bf16 instead of forced FP32.
- The launch script sets PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to reduce allocator fragmentation.

Preflight result:
- High-only single-GPU preflight completed 5 optimizer steps on physical GPU7 with finite loss and gradients.
- The preflight confirmed lora_chunk_size=1024 and lora_dtype=bfloat16.
- No physical GPU0 training use was observed; GPU0 remains reserved for TDW / DISPLAY=:8.

Formal run:
- Formal high-branch resume was started in tmux session stageA_v5_high_resume_oomfix_20260622_122116.
- Output root: local_assets/experiments/exp_stageA_v5_datafix_train_gate/formal_stageA_high_resume_oomfix_snapshot_20260620_144547_20260622_122116
- The run uses CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7, so rank-local cuda:0 maps to physical GPU1, not physical GPU0.
- StageB, DPO, reward, rollout and pair mining were not run.

## 2026-06-22 Implementation Status Correction

The old Base low/high StageA implementation path is no longer active. The current implementation target is LingBot-World-Fast high-only StageA.

Implemented and tested:

- Fast-only guard in runner/config.
- Base policy rejection for Fast StageA.
- `high_only` timestep sampling and fixed validation seed stability.
- CLI overrides for `val_every_optimizer_steps` and `fixed_val_sample_count`.
- Final run logging preserves `branch_mode=high_only`.
- Single-GPU, two-GPU DDP and seven-GPU DDP preflights passed.

Still pending:

- Balanced generated_v5 immutable snapshot.
- Formal high-only StageA run on that snapshot.
- Final loss-normal gate and generation smoke.


## Prefix-5 Pair Rebuild Status (2026-06-27 03:24:08)

- Old anchored pairs were I2V-1 / first-image conditioned, not V2V-5.
- New manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`.
- Pair count: `50`.
- Valid prefix5 pair count: `50`.
- Prefix clips use frames 0-4; winner/loser futures use frames 5-80.
- DPO loss/reward masks are `5..80`.
- Real DPO remains blocked until LingBot-Fast winner/loser energy backend and BF16 DDP preflight are available.


## 2026-06-28 DPO Objective Ablation S0

- S0_sanity_8 and S_localdpo_16 completed with real LingBot-Fast V2V-5 energy.
- Runtime/BF16 path was stable for Standard, SDPO-style, Linear-DPO-style, and LocalDPO-style diagnostics.
- Research signal failed: losses stayed near 0.693, Standard/Linear/LocalDPO showed winner-worse or loser-only behavior, and SDPO-style was only borderline at final step but failed mean winner-preservation gate.
- S1_probe_20 was not launched.
- No StageB, GRPO, large-scale DPO, or full-data StageA was run.
- Report: docs/dpo_objective_ablation_report.md