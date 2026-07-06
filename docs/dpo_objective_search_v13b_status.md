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
