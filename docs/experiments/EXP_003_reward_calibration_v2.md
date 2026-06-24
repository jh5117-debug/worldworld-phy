# EXP_003 Reward Calibration v2

Updated: 2026-06-24 12:47:51 CST  
Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`  
Branch: `research/quant-small-lora-dpo-probe-20260624`  
Start commit: `63d1b93`  

This PRD is written before experiment launch. It must be updated after results are parsed and before the next stage is considered complete.


## Problem and Hypothesis

Epipolar/C-SGC alone produced clean-over-corrupt R_geo ordering of 0.50, below the 0.85 DPO-ready gate. Simulator-grounded trajectory, mask, identity, event, and camera metrics are required.

## Unique Variable

Reward metric suite and calibration corruptions. No model training.

## Inputs

Use Physion/TDW simulator GT: RGB, depth, ID mask, camera poses, intrinsics, object states, event metadata.

## Metrics

Trajectory ADE/DTW/endpoint/timing, Mask IoU/st-IoU, RAFT known-camera BRC, CAF, DINO/V-JEPA FG-ID if backend available, object deformation, physics event timing, reobserve, freeze, quality.

Backend-missing metrics must be marked missing, not faked.

## Corruptions

background_drift, nonrigid_background_warp, wrong_camera, object_deformation, object_identity_change, remove_object, duplicate_object, freeze_foreground, freeze_camera, global_freeze, reobserve_mismatch.

## Gate

- overall clean > corrupted >= 0.85
- corresponding metric ordering >= 0.80
- only passing metrics may be used for DPO pair selection

## Outputs

- `reports/reward_calibration_v2/`
- `docs/reward_calibration_v2_report.md`

## Stop Conditions

Stop using any metric for pair selection if it fails calibration. Continue diagnostics for failed metrics.

## Git Commit

Post-calibration commit: `Calibrate reward and build anchored DPO probe pairs`.

## Status

PLANNED_PRELAUNCH.
