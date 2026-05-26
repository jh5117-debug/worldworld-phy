# Implementation Status

Completed in first-stage skeleton:

- New branch `cam-physgeo-dpo-refactor`.
- `cam_physgeo` package with data, reward, DPO, TRD, training, eval, and utility modules.
- Configs under `configs/cam_physgeo` with `MOVING_CAM_ROOT`.
- Read-only audit and dry-run scripts.
- Safe delete script written but not executed.
- Storage audit and cleanup manifests written.
- Research and project refocus docs written.

Not yet implemented:

- Real optical-flow/depth/DINO/V-JEPA reward extraction for generated rollouts.
- Real LingBot model loading and training loops.
- Actual corrupted video rendering.
- HDF5 key-level decoder for simulator depth/ID/camera fields.
