# Reward Feature Backend Blockers

## DINOv2

- Path checked: `local_assets/weights/dinov2`
- Local checkpoint files: none.
- Load test: `fallback_proxy_only`.
- Impact: `R_fg` and reobserve object/background feature terms are not real DINO features.
- Needed: a small DINOv2 checkpoint under `local_assets/weights/dinov2`.
- Download note: do not download without explicit size/path approval in a later task.

## V-JEPA2 / VideoMAE2

- V-JEPA-like path: `local_assets/weights/vjepa2`.
- File count: 1.
- Size: about `1.66GB`.
- Load test: `path_present_not_loaded`.
- VideoMAE2: not present.
- Impact: temporal/reobserve features remain proxy-only.
- Needed: a real loader smoke for the existing V-JEPA-like checkpoint, or a VideoMAE2 checkpoint and loader.

## Optical Flow

- Optical-flow assets exist in `local_assets/weights/optical_flow`, but no RAFT/GMFlow/WAFT forward is wired into reward.
- Current `R_bg`, `R_cam`, and `P_freeze` use frame-diff proxy.
- Impact: camera-following and freeze conclusions are unreliable, and clean GT can be penalized incorrectly.

## Current Backend Gate

`score_video --require_feature_backend true` records:

```text
feature_backend_requirement.met = false
```

The reward path is honest about the missing backends, but it is still not reliable enough for DPO pair selection.
