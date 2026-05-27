# Reward Implementation Report: Physion

Implemented reward modules:

- `R_bg`: background rigid consistency proxy with known-camera/depth interface.
- `R_cam`: camera adherence proxy using pose motion and video motion.
- `R_fg`: foreground identity/shape proxy with ID-mask hooks.
- `R_phys`: template-aware physical event proxy.
- `R_reobs`: first/last visible segment proxy for reobserve motions.
- `R_quality`: blur, brightness, flicker, saturation proxy.
- `P_freeze`: freeze penalty using expected camera motion and video motion.

For clean/corrupted Physion GT, the pipeline uses HDF5 camera/depth/ID/object-state metadata when available and video-space proxies otherwise. For generated rollouts without depth/ID, it falls back to frame-diff and quality proxies and marks this as non-final reward behavior.

Corrupted negative types implemented:

- background_drift
- nonrigid_background_warp
- object_deformation
- object_color_identity_change
- freeze_foreground
- freeze_camera
- global_freeze
- wrong_camera_motion
- camera_shuffle
- reobserve_mismatch
- remove_object
- create_object
