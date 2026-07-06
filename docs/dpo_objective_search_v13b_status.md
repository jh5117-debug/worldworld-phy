# DPO Objective Search v13b Status

Updated: 2026-07-06T13:08:17+08:00

## Current State

- Experiment: `EXP_dpo_objective_search_v13b`.
- Repo branch: `research/quant-small-lora-dpo-probe-20260624`.
- Required data entry remains `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`; old `ready_500` is not used.
- v13b implementation is prepared for 6-10 small objective variants with gap logging.
- Subsets generated under `manifests/dpo_v13b_subsets/`.
- Direct smoke passed for subset builder, scheme dry-run, gap metrics, and GPU4/5 gate helper.
- `pytest` is unavailable in the system Python, so validation used `compileall` plus direct smokes; no pytest PASS is claimed.

## GPU Status

- User restriction: only physical GPU4 and GPU5 are allowed.
- GPU0/1/2/3/6/7 are forbidden for this round.
- Independent `nvidia-smi pmon` snapshot showed GPU4 and GPU5 occupied by existing non-v13b `python` jobs.
- Scheduler dry-run decision: `GPU4_5_BLOCKED`.
- No v13b training job was launched.
- No forbidden GPU was used by v13b.

## Implementation Status

Implemented:

- `cam_physgeo/dpo/gap_metrics_v13b.py`
- `cam_physgeo/dpo/dpo_v13b_subset_builder.py`
- `cam_physgeo/dpo/dpo_objective_search_v13b.py`
- `cam_physgeo/orchestration/gate_checks_v13b.py`
- `cam_physgeo/orchestration/gpu_scheduler_v13b.py`
- `configs/cam_physgeo/dpo_objective_search_v13b.yaml`
- `scripts/launch_dpo_objective_search_v13b.sh`
- v13b tests/direct-smoke files.

Objective runner patched to log win/lose gaps and normalized gaps, and to support `no_lose_gap_normalized_win_only` and `normalized_clipped_loser` objectives.

## Decision

`DPO_RECIPE_GPU_BLOCKED`

The search code is ready, but training must wait until GPU4 or GPU5 is idle. Do not fall back to GPU6/7 or GPU0-3.

## What Was Not Run

- No large DPO.
- No train400.
- No S32/S64.
- No StageA / StageB / GRPO.
- No broad-LoRA.
- No checkpoint/data/weight deletion.
- No videos or weights pushed.

## Interim Update - 2026-07-06T15:32:53

- S01 and S02 were run only with physical GPU4/5 via explicit `CUDA_VISIBLE_DEVICES=4` / `CUDA_VISIBLE_DEVICES=5`.
- No v13b process used GPU0/1/2/3/6/7.
- S01/S02 reached an early healthy training-signal window and were stopped before launching more schemes so checkpoint video/metrics/audit gates can be evaluated.
- Current best training-signal candidate: `S01_winner_detached_pref_low`.
- Evidence is summarized in `reports/dpo_objective_search_v13b/search_summary.md` and `reports/dpo_objective_search_v13b/gap_health_by_scheme.csv`.
- This is not a valid DPO recipe yet: checkpoint V2V-5 videos, metrics, and Codex visual audit are pending.
- Checkpoint eval hit the known WanI2VFast / `WanModelFast.from_pretrained` initialization bottleneck before videos were produced.
- `cam_physgeo/eval/run_fast_adapter_inference.py` now patches `WanModelFast.from_pretrained` to force local safetensors / low CPU memory loading for future eval attempts.
- GPU4/5 are currently occupied by older overnight rollout/eval processes, so v13b checkpoint eval is waiting rather than killing unknown or non-current jobs.

Current decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY`; train400 and large DPO remain blocked.

## GPU4/5 Checkpoint Eval Waiter - 2026-07-06T15:45:53

- A non-destructive waiter was launched for `S01_winner_detached_pref_low` checkpoint eval.
- Script: `reports/dpo_objective_search_v13b/S01_winner_detached_pref_low/checkpoint_eval/run_s01_eval_when_gpu45_free.sh`.
- PID file: `reports/dpo_objective_search_v13b/S01_winner_detached_pref_low/checkpoint_eval/wait_eval.pid`.
- Heartbeat: `reports/dpo_objective_search_v13b/S01_winner_detached_pref_low/checkpoint_eval/wait_eval_state.jsonl`.
- The waiter only permits physical GPU4/5 and waits until there are no compute PIDs and memory is below the idle threshold.
- At launch, GPU4/5 were occupied by older overnight rollout/eval jobs, so no v13b checkpoint eval was started yet.
- No unknown/non-current process was killed.

## Checkpoint Eval Schema Repair - 2026-07-06T16:47:05

- Safe Wan loading reached shard load and LoRA application for S01 step050.
- The first post-loader eval attempt failed on manifest schema: `val_video_4.jsonl` is a nested DPO pair manifest, while the eval wrapper expected flat condition rows.
- `cam_physgeo/eval/run_fast_adapter_inference.py` now supports nested `condition.*` and `winner.*` fields directly.
- Direct helper smoke on `manifests/dpo_v13b_subsets/val_video_4.jsonl` resolves sample id, prompt, image, poses, intrinsics, action directory, and source video.
- A single-instance GPU4/5 waiter is running and will retry S01 step050 once GPU4 or GPU5 is actually idle.
- Current decision remains `DPO_RECIPE_TRAINING_SIGNAL_ONLY`; checkpoint videos, metrics, and Codex visual audit are not complete.
## Final v13b Update - 2026-07-07

Status: COMPLETE - DPO_RECIPE_NOT_FOUND. Only physical GPU4/GPU5 were used for v13b jobs; GPU0-3/6/7 were not used. S07 had the best training signal but failed the checkpoint metric gate because VBench temporal_flickering worsened. S03/S06/S09 were winner-positive and non-loser-dominant, but DPO loss stayed near 0.693 and preference utility stayed near zero. S10 camera+temporal LoRA timed out before first row. Scale remains blocked: no S16/S32/S64/train400.

