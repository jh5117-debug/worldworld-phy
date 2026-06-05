# TDW Generation v2 Visible-Motion 10-Sample GPU0 Actual Report

Date: 2026-06-05

## Approval

The user explicitly approved GPU0-bound `DISPLAY=:8` for this 1 -> 10 visible-motion smoke only.

No 50 / 200 / 1k generation was run.

## Generation

| Item | Value |
|---|---|
| Generation status | passed |
| Return code | 0 |
| HDF5 generated | 10 / 10 |
| Validation OK | 10 / 10 |
| Suitable for warmup | 10 / 10 |
| Suitable for visible motion | 5 / 10 |
| Too static | 2 / 10 |
| Too extreme | 3 / 10 |
| GPU / display | GPU0, `DISPLAY=:8` |

## Template Distribution

| Template | Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

## Camera Variant Distribution

| Camera variant | Count |
|---|---:|
| orbit_left_24 | 2 |
| orbit_right_24 | 2 |
| orbit_left_28 | 1 |
| orbit_right_28 | 1 |
| strafe_left_050 | 1 |
| strafe_right_050 | 1 |
| dolly_in_025 | 1 |
| dolly_out_025 | 1 |

## Motion Metrics

| Metric | Value |
|---|---:|
| Camera path min | 0.25179353072490596 |
| Camera path avg | 1.0406294554992068 |
| Camera path max | 1.777591354401351 |
| Background motion min | 0.010914065726948056 |
| Background motion avg | 0.02068891406101598 |
| Background motion max | 0.029444030179134148 |
| Target visible ratio | 1.0 / 1.0 / 1.0 |
| Max invisible frames | 0 |

## Accepted Samples

| Sample | Template | Camera | Camera path | Background motion | Contact sheet |
|---|---|---|---:|---:|---|
| `00000_drop_orbit_left_24_seed22000` | drop | `orbit_left_24` | 1.1854358679765697 | 0.029444030179134148 | `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_24_seed22000_0000_contact_sheet.jpg` |
| `00001_drop_orbit_right_24_seed22001` | drop | `orbit_right_24` | 1.1854358468400403 | 0.025500216013328594 | `local_assets/data/physion/generated_v2/reports/contact_sheets/00001_drop_orbit_right_24_seed22001_0000_contact_sheet.jpg` |
| `00002_drop_orbit_left_28_seed22002` | drop | `orbit_left_28` | 1.383121614614001 | 0.022707375094548544 | `local_assets/data/physion/generated_v2/reports/contact_sheets/00002_drop_orbit_left_28_seed22002_0000_contact_sheet.jpg` |
| `00004_collision_strafe_left_050_seed22004` | collision | `strafe_left_050` | 0.5015974678033599 | 0.019690681672231716 | `local_assets/data/physion/generated_v2/reports/contact_sheets/00004_collision_strafe_left_050_seed22004_0000_contact_sheet.jpg` |
| `00005_collision_strafe_right_050_seed22005` | collision | `strafe_right_050` | 0.5015974678023923 | 0.019437880731526424 | `local_assets/data/physion/generated_v2/reports/contact_sheets/00005_collision_strafe_right_050_seed22005_0000_contact_sheet.jpg` |

## Rejected Samples

| Sample | Reason |
|---|---|
| `00003_collision_orbit_right_28_seed22003` | `too_extreme`; camera path 1.5903365420926159 exceeded the 1.50 threshold |
| `00006_roll_dolly_in_025_seed22006` | `too_static`; camera path 0.25179353072490596 below the 0.45 threshold |
| `00007_roll_dolly_out_025_seed22007` | `too_static`; camera path 0.25179353072888294 below the 0.45 threshold and background motion 0.010914065726948056 below threshold |
| `00008_containment_orbit_left_24_seed22008` | `too_extreme`; camera path 1.777591354401351 exceeded the 1.50 threshold |
| `00009_containment_orbit_right_24_seed22009` | `too_extreme`; camera path 1.7775913320079475 exceeded the 1.50 threshold |

## Visual Review

Manual contact-sheet review agreed with the validator:

- accepted orbit and strafe samples show visible camera/parallax motion;
- dolly samples remain visually weak;
- containment orbit samples move too much under the current path-length threshold and need separate tuning before warmup expansion.

## Decision

The visible-motion smoke is a partial pass: the pipeline and 5 accepted samples demonstrate the direction, but the profile should be tuned before a 50-sample run.
