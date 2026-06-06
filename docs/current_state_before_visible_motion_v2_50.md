# Current State Before visible-motion v2 50

Branch before this run: `physion-tdw-visible-motion-v2-run`

Previous v2 10-sample smoke:

- generated HDF5: 10/10
- validation OK: 10/10
- suitable for visible motion: 10/10
- rejected: 0/10
- camera path length min/avg/max: 0.5016 / 0.9790 / 1.3831
- background motion proxy min/avg/max: 0.0120 / 0.0204 / 0.0295
- LingBot cam-only conversion: 10/10
- `target.mp4` probe: passed
- `use_action=false`, dummy zero `action.npy`

Reason v2 was ready for 50:

- v2 acceptance exceeded the required 8/10 threshold.
- Every template had accepted samples.
- v1 template-specific failures were fixed by template-aware camera mapping.

Approval scope for this run:

- GPU0-bound `DISPLAY=:8` approved for exactly one `warmup_visible_motion_v2` 50-sample validation.
- No 200 / 1k.
- No training, DPO, VideoGPA `03_train`, Stage1, rollout, or reward calibration.

