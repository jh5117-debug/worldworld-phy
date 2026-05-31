# Feature Backend Repair Plan

No model downloads were performed in this round.

## DINOv2

Check result:

- Path: `local_assets/weights/dinov2`
- Found directory: yes
- File count: `0`
- Load test: `fallback_proxy_only`
- Current impact: `R_fg` and `R_reobs` cannot use real foreground/reobserve features.

Recommended minimal checkpoint:

- A small DINOv2 backbone such as `dinov2_vits14`.
- Expected size: roughly hundreds of MB depending on format.
- Target path: `local_assets/weights/dinov2/`.
- Requires network/HF or torch hub access unless weights are already available elsewhere.
- User approval should be requested before any download.

## V-JEPA / VideoMAE

Check result:

- `local_assets/weights/vjepa2` exists and contains one checkpoint-like file.
- Size: about `1.664 GB`.
- Load test: `path_present_not_loaded`.
- Current impact: temporal/reobserve/TRD-style feature scoring remains proxy-only.

Next action:

- Add a real forward adapter for the existing V-JEPA-like checkpoint if its config and architecture are known.
- If that checkpoint is incompatible, consider a small VideoMAE2 checkpoint under `local_assets/weights/videomae2/`, with user approval before download.

## Optical Flow

Current state:

- Optical flow assets exist under `local_assets/weights/optical_flow`, but reward does not call a real RAFT/GMFlow/WAFT forward pass.
- `R_bg`, `R_cam`, and `P_freeze` rely on frame-diff proxies.

Next action:

- Inventory the exact optical-flow checkpoint and repo code in `local_assets/weights/optical_flow`.
- Wire a small forward smoke into `cam_physgeo/rewards/geometry.py`, `camera_following.py`, and `freeze_penalty.py`.
- If no compatible checkpoint exists, request approval before downloading RAFT/GMFlow/WAFT weights.

## Reward Terms Affected

- `R_fg`: needs DINOv2 + ID mask.
- `R_reobs`: needs DINOv2/V-JEPA/VideoMAE plus reobserve visibility logic.
- `R_bg`: needs depth/camera + optical flow or simulator depth for clean GT.
- `R_cam`: needs known camera-induced flow or real optical flow.
- `P_freeze`: needs real flow/mask-aware motion, not raw frame difference.
- `R_phys`: needs object-state / ID-mask event logic, not frame motion proxy.
