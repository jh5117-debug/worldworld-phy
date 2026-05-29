# Reward Feature Backend After Fast Rollout Report

## Backend Checks

Feature backend checks ran after the Fast rollout smoke.

### DINOv2

- Path checked: `local_assets/weights/dinov2`
- Local checkpoint files: 0
- Load test: `fallback_proxy_only`
- Status: not a real DINOv2 forward path yet
- Impact: `R_fg` and `R_reobs` cannot be trusted as DINO-based identity/reobserve metrics.

### V-JEPA2 / VideoMAE2

- Path checked: `local_assets/weights/vjepa2` and `local_assets/weights/videomae2`
- Local V-JEPA-like file count: 1
- Size: about 1.66 GB
- Load test: `path_present_not_loaded`
- Status: adapter path exists, but the smoke intentionally did not load/run the large teacher.
- Impact: temporal feature reward remains proxy-only in this path.

### Optical Flow

- Status: real RAFT/GMFlow/WAFT forward is not wired in this reward path.
- Current reward uses frame-diff/proxy motion signatures.
- Impact: `R_bg`, `R_cam`, and `P_freeze` remain provisional.

## score_video Backend Requirement

`score_video --require_feature_backend true` wrote `feature_backend_requirement.met=false`.

Reason:

- DINO/V-JEPA hooks are present, but real frozen-feature forward is not implemented for this smoke path.
- Reward records this state so rollout sensitivity is not overstated.

## Conclusion

The feature backend smoke confirms that the code reports backend status honestly, but it does not confirm real DINO/V-JEPA/flow scoring. Any reward-on-rollout conclusion from this round is provisional and should not be used for DPO pair selection yet.
