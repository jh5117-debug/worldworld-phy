# StageA Evaluation, Geometry Metrics, BF16 Readiness Final Report

## SSH / Git

- H20 repo path: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`
- Branch: `research/stageA-eval-sgc-epipolar-bf16-20260623`
- Start commit for this continuation: `7631276`
- Code/eval commit: `443bf98`
- BF16 readiness commit: `c2b7c23`
- Push status: pushed to `origin/research/stageA-eval-sgc-epipolar-bf16-20260623`

## Meeting Evaluation

- Evaluation root: `local_assets/meeting_eval_20260624_011137`
- Compared models: Original LingBot-Fast, StageA step800 adapter, StageA final883 adapter.
- Samples: 8 total, 2 each for drop / collision / roll / containment.
- All compared videos used the same initial image, prompt, poses, intrinsics, seed, scheduler, 81 frames, and 480x832 resolution.
- Contact sheets: `local_assets/meeting_eval_20260624_011137/contact_sheets/`
- Qualitative CSV: `reports/meeting_eval_20260624_011137/qualitative_scores.csv`

Result: StageA optimization is `PASS`, but generation quality is `FAILED_OR_MIXED`. StageA did not provide a stable visual win over Original Fast; foreground identity and physics remain weak.

## Quantitative Training Results

- Training metrics: `reports/meeting_eval_20260624_011137/metrics/`
- Parsed optimizer steps: 883
- Fixed-val step100 to step800 relative drop: about 35.4%.
- Non-finite loss count: 0.
- Target overshoot root cause: old epoch-boundary target gate; fixed by commit `7631276`.

## Epipolar + C-SGC

- Implemented: `cam_physgeo/rewards/epipolar.py`
- Implemented: `cam_physgeo/rewards/conditioned_sgc.py`
- Tests: `tests/test_epipolar_metric.py`, `tests/test_conditioned_sgc.py`
- Clean/corrupt calibration: `reports/meeting_eval_20260624_011137/reward_calibration.csv`
- Generated-video geometry summary: `reports/meeting_eval_20260624_011137/generated_geometry_summary.csv`

Status: `PRELIMINARY/BLOCKED_FOR_DPO_REWARD`. The clean-over-corruption ordering target was not met, so these are diagnostics, not DPO-ready reward terms.

## BF16 Readiness

- BF16 root: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/bf16_formal_readiness_20260624_012335`
- Matrix: `reports/meeting_eval_20260624_011137/bf16_preflight_matrix.csv`
- Speed benchmark: `reports/meeting_eval_20260624_011137/bf16_speed_benchmark.csv`
- Report: `docs/fast_bf16_formal_readiness_report.md`

Status: `BF16_FORMAL_READY`.

Completed:

- Single GPU7 BF16: 20/20, finite fixed-val, no SIGFPE/OOM/NaN.
- DDP2 GPU6,7 BF16: 20/20, finite fixed-val, no SIGFPE/OOM/NaN.
- DDP7 GPU1-7 BF16: 20/20, finite fixed-val, no SIGFPE/OOM/NaN.
- Safe LoRA-FP32/autocast-disabled comparison: 8/8, finite fixed-val.

## Full-Data StageA Prep

- Current main generated_v5 audit: 3999 raw HDF5, 3299 converted/stage1-ready clips.
- Immutable partial snapshot: `local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/`
- Train / val / test_holdout: 2804 / 329 / 166.
- Config prepared: `configs/cam_physgeo/fast_stageA_full_high_only.yaml`
- Launch script prepared: `scripts/launch_fast_stageA_full_high_only.sh`
- Long full-data StageA was not launched in this task.

## Safety Confirmation

- GPU0 was not used for training/evaluation.
- Existing TDW generation sessions were not killed or modified.
- StageB was not run.
- DPO / GRPO was not run.
- Reward pair mining was not run.
- No local_assets, reports videos, HDF5, MP4, NPY, checkpoints, or model weights were committed.
