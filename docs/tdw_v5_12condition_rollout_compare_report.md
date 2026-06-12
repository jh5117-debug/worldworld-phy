# TDW v5 12-Condition Rollout Compare Report

Date: 2026-06-12

## Setup

- Conditions: 12 total, selected from the TDW v5 200 test split.
- Templates: drop / collision / roll / containment.
- Variants generated:
  - Base LingBot-Fast
  - Stage A adapter
  - Stage B adapter
- Output root:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/12condition_base_stageA_stageB`

## Important Runtime Fix

The first adapter rollout attempt failed after base generation because the adapter checkpoint path was passed as a directory. The runtime expected a file and raised:

`IsADirectoryError: adapter checkpoint path is a directory`

Fix:

- `cam_physgeo/eval/run_inference.py` now resolves adapter checkpoint directories to `adapter_state.pt`.
- Base 12/12 outputs were preserved.
- Adapter rollout was retried without rerunning base.

## Result

- Base generated videos: 12 / 12.
- Stage A adapter generated videos: 12 / 12.
- Stage B adapter generated videos: 12 / 12.
- Total generated videos: 36.
- Failures after retry: 0.
- Camera condition passed to pipeline: yes, via LingBot-Fast `action_path` compatibility path containing poses/intrinsics.

## Notes

- The retry summary records adapter results only, but the rollout root contains all three variants.
- Reward scoring scans the rollout root and therefore includes Base, Stage A, Stage B, and clean GT.
- This rollout was expensive because the current wrapper launches one LingBot-Fast process per video and reloads the model each time.

## Gate

Rollout comparison passed at the file/probe level. Reward confidence is handled separately in the reward report.

