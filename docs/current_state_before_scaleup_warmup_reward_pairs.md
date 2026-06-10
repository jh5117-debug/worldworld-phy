# Current State Before Scale-Up / Warmup / Reward Pairs

Date: 2026-06-10

## Completed Gates

- Current main warmup candidate: TDW v5 aggressive 2x 200, human-approved.
- LingBot cam-only conversion: 200/200.
- Manifest/split gate: all 200 samples registered; train/val/test = 160/20/20.
- Dataloader smoke: passed with video, poses, intrinsics, dummy action, and `use_action=false`.
- True LingBot-Fast forward-loss gate: passed with real WanI2VFast, VAE, scheduler, and camera condition path.
- Balanced Stage A high-noise warmup: passed 60/60 steps with balanced template coverage.
- Balanced Stage A adapter checkpoint exists: `local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`.

## Remaining Gates

- TDW scale-up: not run in this turn. TDW still requires an Xorg display; only GPU0-bound `DISPLAY=:8` has been confirmed in prior audits, and this request did not approve GPU0 for TDW.
- Longer Stage A warmup: not run. The prior 60-step run took about 9028 seconds, so a 300-step run is expected to exceed the 12-hour approval threshold.
- Base-vs-adapter rollout: not run. The code path previously lacked adapter checkpoint loading for inference; this branch adds the missing runtime LoRA load path.
- Base-vs-adapter rollout dry-run: passed for 4 balanced conditions, one per template.
- Reward scoring / winner-loser pair construction: not run because rollout videos were not produced in this turn.

## Code Readiness

- `cam_physgeo/eval/run_inference.py` now accepts an adapter checkpoint and can inject the saved Stage A runtime LoRA before LingBot-Fast generation.
- `cam_physgeo/eval/rollout_compare_base_adapter.py` now selects balanced manifest conditions and runs base plus adapter rollouts through the existing LingBot-Fast runtime.
- `cam_physgeo/rewards/score_rollouts.py` now scores GT/base/adapter videos and records generated-video backend confidence.
- `cam_physgeo/dpo/build_reward_pairs.py` now builds reward-filtered pair manifests only when margins and confidence pass.

## Current Decision

Use existing v5 200 and the existing balanced Stage A adapter as the next rollout candidate, but do not launch 12-condition base-vs-adapter rollout without explicit long-runtime approval.
