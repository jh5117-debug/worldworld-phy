# Reward Feature Backend Actual Status

## DINOv2

- Path checked: `local_assets/weights/dinov2`.
- Directory exists, but file count is 0.
- Actual forward: not available.
- Current fallback: deterministic proxy visual feature signature.
- Impact: `R_fg` and `R_reobs` should not be treated as real DINO-based identity scores yet.

## V-JEPA2 / VideoMAEv2

- Path checked: `local_assets/weights/vjepa2` and `local_assets/weights/videomae2`.
- V-JEPA-like checkpoint exists, about 1.66G.
- Actual forward: not run; smoke only verified path presence.
- Current fallback: deterministic proxy temporal/color feature.
- Impact: TRD/reobserve temporal feature is not yet a real V-JEPA/VideoMAE forward path.

## Optical Flow

- Optical-flow assets exist under `local_assets/weights/optical_flow`.
- Actual RAFT/GMFlow/WAFT forward: not wired.
- Current fallback: frame-difference motion proxy.
- Impact: `R_bg`, `R_cam`, and `P_freeze` are useful for smoke but not final rigid-flow reward.

## Score-Video Backend Check

Command with `--require_feature_backend true` scored 3 samples and wrote `local_assets/reports/smoke/reward_feature_backend_check.jsonl`.

- `feature_backend_required`: true.
- `feature_backend_met`: false.

Conclusion: reward currently records backend absence honestly. It is not yet a real DINO/V-JEPA/optical-flow reward stack.

