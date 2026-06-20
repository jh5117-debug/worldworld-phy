# GitHub Push Report

Pending push for `research/stageA-v5-datafix-train-20260620`. This file will be updated after `git push`.


## StageA Fixed-Val Patch Push (2026-06-20 19:25 CST)

- Previous pushed data/conversion/training-gate commit: `a33b559179c0b64a4b601eeb43d932e9f4318b97`.
- Additional fixed-val trainer patch prepared after discovering that the first formal StageA run lacked true fixed validation forward-loss.
- This patch adds fixed validation metrics and loss gate integration; no local_assets, generated data, videos, checkpoints, or large logs are staged.

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

<!-- STAGEA_V5_DOC_PUSH_20260621_START -->
## 2026-06-21 StageA documentation push

- Pushed branch: `research/stageA-v5-datafix-train-20260620`
- Documentation status commit pushed before this push-report update: `28e3d19817e8e721ae9b138fc57feec0b31d7e28`
- Push time recorded on H20: `2026-06-21T02:15:22+08:00`
- Scope: Markdown-only status update for StageA v5 data gate, preflight, formal run launch, monitor tmux, and RUNNING_NOT_FINAL state.
- Explicit exclusions: no `local_assets`, no HDF5/MP4/NPY, no checkpoints, no adapter weights, no large logs.
- Training state at documentation time: formal StageA running on physical GPU1-7; TDW tmux sessions preserved; GPU0 not used for training.
<!-- STAGEA_V5_DOC_PUSH_20260621_END -->

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
