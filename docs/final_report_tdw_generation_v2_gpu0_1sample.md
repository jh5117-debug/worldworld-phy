# Final Report: Approved GPU0 TDW 1-Sample Smoke

## 1. Actual Generation

No actual TDW sample was generated.

The user approved `DISPLAY=:8` / GPU0 for exactly one `warmup_mild` sample. The wrapper was launched under that approval, but it failed before TDW/Unity scene generation.

## 2. Display / GPU

- Display: `:8`
- Bound GPU: GPU0
- Approval: explicit user approval for one sample only
- 10/50 samples: not run
- Training/DPO/VideoGPA/Stage1: not run

## 3. GPU Usage

GPU0 returned to minimal/idle memory after the failed wrapper startup. No persistent TDW/Unity process remained.

## 4. HDF5 / Video / Contact Sheet

- HDF5 path: none
- MP4 path: none
- contact sheet path: none
- generated file count: 0

## 5. Validation

Validation was run after the failure:

- HDF5 count: 0
- validation ok count: 0
- suitable_for_warmup: 0

No `target_visible_ratio`, foreground disappearance, camera magnitude, or HDF5 key completeness could be measured because no sample exists.

## 6. Failure Details

Attempt 1:

- return code: 2
- blocker: wrapper path was relative and could not be found after subprocess cwd changed
- fix: use absolute output root and absolute wrapper path

Attempt 2:

- return code: 1
- blocker: generated wrapper Python source contained JSON `false`
- fix: parse mild variant JSON with `json.loads(...)`

Neither failure launched a successful TDW scene or produced data.

## 7. LingBot Conversion

Skipped. No accepted TDW v2 sample exists.

## 8. Next-Step Gate

Do not run 10 samples yet.

The next minimal action is to re-run exactly one `warmup_mild` TDW sample after the wrapper fixes are synced to H20 and confirmed. This requires user confirmation because the previous approved one-sample run has already failed and stopped.

## 9. Safety

- no training
- no DPO
- no VideoGPA
- no Stage1
- no LingBot rollout
- no reward calibration
- no 10/50 generation
- no `local_assets` committed

