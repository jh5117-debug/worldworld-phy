# Final Report: TDW visible-motion v2 Run

## v1 Summary

`warmup_visible_motion` v1 generated 10 samples and validated HDF5/key completeness for 10/10, but only 5/10 passed `suitable_for_visible_motion`.

Rejected reasons:

- collision + orbit_right_28: too extreme by camera path.
- roll + dolly_in_025: too static.
- roll + dolly_out_025: too static and low background motion.
- containment + orbit_left_24: too extreme.
- containment + orbit_right_24: too extreme.

## v2 Sync

Remote run worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work`

The worktree was created from `origin/physion-tdw-visible-motion-v2` at commit `c8ac7b2b653b177a942d815148ef663615346d20`, then linked to the shared `local_assets` directory. The helper worktree contains `warmup_visible_motion_v2`.

## v2 Actual

Approved resource scope:

- GPU0-bound `DISPLAY=:8`
- exactly one 10-sample `warmup_visible_motion_v2` smoke
- no 50 / 200 / 1k

Results:

- Generated HDF5: 10/10
- Validation OK: 10/10
- Accepted / suitable for visible motion: 10/10
- Rejected: 0/10
- Per-template accepted: drop 3, collision 3, roll 2, containment 2
- Camera path length min/avg/max: 0.5016 / 0.9790 / 1.3831
- Background motion proxy min/avg/max: 0.0120 / 0.0204 / 0.0295
- Target visible ratio: 1.0 for every sample
- Max invisible frames: 0 for every sample
- `too_static`: 0
- `too_extreme`: 0

Converted samples:

- LingBot cam-only conversion: 10/10
- `target.mp4` probe: passed by converter
- `use_action=false`
- dummy zero `action.npy`

Video deliverables were updated in shared `local_assets`:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

## 50 Readiness

Ready to request a 50-sample `warmup_visible_motion_v2` validation because:

- acceptance is 10/10, above the 8/10 threshold;
- every template has at least one accepted sample;
- no visible-motion rejection occurred.

The 50 run is not approved by this report. User approval is required, especially because the current TDW route uses GPU0-bound `DISPLAY=:8`.

## Safety

- No training.
- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No LingBot rollout.
- No reward calibration.
- No 50 / 200 / 1k generation.
- No `local_assets` committed.
- No generated HDF5 / MP4 / NPY committed.

