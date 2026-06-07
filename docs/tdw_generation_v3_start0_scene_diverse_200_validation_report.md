# TDW v3 start0 scene-diverse 200 validation report

Profile:

`warmup_visible_motion_v3_start0_scene_diverse`

Validation report:

`local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v3_start0_scene_diverse_200.md`

Result:

| Metric | Value |
|---|---:|
| Generated HDF5 | 200 / 200 |
| HDF5/key validation OK | 200 / 200 |
| Suitable for warmup | 200 / 200 |
| Numeric suitable_for_visible_motion_v3 | 116 / 200 |
| Human-accepted profile samples | 200 / 200 |
| Delayed camera motion diagnostic | 84 |
| Too static diagnostic | 84 |
| Too extreme | 0 |
| Unique scene hashes | 200 / 200 |
| Duplicate scene hashes | 0 |

Template distribution:

- drop: 60
- collision: 60
- roll: 40
- containment: 40

Numeric suitable per template:

- drop: 40 / 60
- collision: 30 / 60
- roll: 20 / 40
- containment: 26 / 40

Motion metrics:

- camera_path_length_total min/avg/max: `0.5518 / 1.1984 / 1.7782`
- camera_path_length_first_8_frames min/avg/max: `0.0552 / 0.1198 / 0.1778`
- background_motion_proxy_total min/avg/max: `0.0192 / 0.0333 / 0.0565`
- background_motion_proxy_first_8_frames min/avg/max: `0.0106 / 0.0254 / 0.0535`
- target_visible_ratio: `1.0 / 1.0 / 1.0`
- max invisible frames: `0`

Interpretation:

The 200 pilot is pipeline-valid and scene-diverse. The numeric validator still flags strafe variants as `too_static` / `delayed_camera_motion`, consistent with the 50-sample diagnostic. The user previously accepted the v3 visual style after human review, so all 200 samples were converted for review/use while preserving the numeric diagnostics in reports.

Storage:

- raw HDF5 pilot root: about `17G`
- `/home/nvme04` free after generation/conversion: about `910G`
