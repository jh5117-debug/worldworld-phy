# Visible-Motion v2 Sync Report

Helper/run worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work`

Sync method:

- A fresh detached remote worktree was created from `origin/physion-tdw-visible-motion-v2`.
- `local_assets` was symlinked to the existing shared asset/data directory.
- The run worktree HEAD was `c8ac7b2b653b177a942d815148ef663615346d20`.

Evidence:

- `configs/cam_physgeo/tdw_generation_v2.yaml` contains `warmup_visible_motion_v2`.
- The generated v2 plan used `drop:3`, `collision:3`, `roll:2`, `containment:2`.
- No roll dolly variants were present.
- No containment orbit 24 / orbit 28 variants were present.

Additional fix applied before final validation:

- `validate_generated_hdf5.py` and `filter_generated_samples.py` now treat any `warmup_visible_motion*` profile as a visible-motion profile.
- `convert_generated_to_lingbot.py` preserves `warmup_visible_motion_v2` in converted metadata when the source path is v2.

The sync and fix succeeded. The earlier SSH instability affected polling only; the actual generation was run in remote `tmux`.

