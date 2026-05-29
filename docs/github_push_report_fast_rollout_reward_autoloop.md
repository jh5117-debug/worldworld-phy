# GitHub Push Report: Fast Rollout Reward Autoloop

- Branch: `physion-fast-rollout-reward-autoloop`
- Remote: `origin`
- Commit message: `Add 10h autoloop for Fast rollout, camera ablation, and reward smoke`
- Large files: not staged; `local_assets/`, generated videos, logs, weights, HDF5, MP4, NPY, NPZ, PT, PTH, and safetensors remain ignored.
- Validation:
  - `python -m compileall -q cam_physgeo`
  - `python tests/test_intrinsics_conversion.py`
  - `pytest -q tests/test_intrinsics_conversion.py`
- Remote smoke run:
  - `local_assets/reports/smoke/fast_rollout_reward_autoloop_20260530_004916`
  - final status: `success`
  - rollout count: `3`
  - ablation variant count: `3`
  - reward valid pairs: `3`
- Push status: successful.
- Remote branch URL: `https://github.com/jh5117-debug/worldworld-phy/tree/physion-fast-rollout-reward-autoloop`

The exact branch head hash is reported in the final assistant summary after commit and push to avoid self-referential report churn.
