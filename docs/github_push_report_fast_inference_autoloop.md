# GitHub Push Report: Fast Inference Autoloop

Branch: `physion-lingbotfast-actual-inference-autoloop`

Commit: branch tip after push; exact hash is reported in the final assistant summary.

Scope:

- Added a bounded LingBot-Fast 1-sample inference autoloop.
- Added a shell wrapper for the autoloop.
- Added a `ready_to_generate` runtime marker.
- Added a per-attempt camera intrinsics adapter from Physion projection matrices to LingBot `[fx, fy, cx, cy]`.
- Added reports documenting the successful 1-sample actual inference smoke.

Not pushed:

- `local_assets/`
- generated videos
- contact sheets
- logs
- weights
- HDF5/MP4/NPY/PT/PTH/safetensors
- checkpoints
- third-party raw repos

Validation:

- `python -m compileall -q cam_physgeo/eval/autoloop_fast_inference.py cam_physgeo/eval/run_inference.py`
- Remote autoloop produced one successful short video and stopped.
