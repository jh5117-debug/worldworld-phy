# Camera Condition Status Correction

Current Status: CAMERA_CONDITION_PATH_CONFIRMED_BUT_SENSITIVITY_PARTIAL

Updated: 2026-06-30 14:21:36

## Previous Misleading Status

The previous v5 Fast support diagnosis used `UNKNOWN` for whether LingBot-Fast strongly uses camera condition and suggested rerunning camera audit as if the camera path itself had not been validated. That wording was misleading.

## Earlier Ablation Evidence

Known earlier camera ablation result:

| comparison | observed difference |
| --- | ---: |
| repeat A vs B | 0.0 |
| correct vs frozen | 0.0 |
| correct vs reversed | 0.02218 |
| correct vs exaggerated_yaw | 0.03502 |
| correct vs exaggerated_translation | 0.03765 |

Search performed in this tree:

- `find docs reports local_assets -iname "*camera*ablation*" -o -iname "*camera*condition*"`
- `rg` for the exact numeric values in `docs` and `reports`

Earlier ablation result is known from prior logs but source report not found in current tree.

## Corrected Status

Camera condition status:

- `CAMERA_CONDITION_PATH_CONFIRMED`
- `CAMERA_SENSITIVITY_PARTIAL`
- `NORMAL_CAMERA_MOTION_RESPONSE_WEAK`
- `STRONG_CAMERA_PERTURBATION_AFFECTS_OUTPUT`

LingBot-Fast / LingBot itself supports camera/control. Strong camera perturbations affect output, so the camera condition path is not completely dead.

## What Still Needs Checking

The unresolved issue is sensitivity and usefulness, not existence:

- ordinary correct-vs-frozen motion response is weak;
- strong reversed / yaw / translation perturbations change output;
- reward and pair mining have not yet turned camera differences into stable human-visible medium-hard preference pairs;
- TypeB rollout negatives remain blur/quality blocked;
- TypeA+/TypeM v5 visual gate found only 3/42 strict DPO-ready pairs.

## Next Experiment Focus

Do not re-prove the camera path from scratch. The next work should focus on reward visual alignment and medium-hard pair construction, with a targeted camera-sensitivity calibration only if it directly helps produce visible camera-related negatives.
