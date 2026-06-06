# TDW Generation v3 Start0 Visible-Motion Profile Report

## Profile

`warmup_visible_motion_v3_start0_scene_diverse`

## Difference Versus v2

v2 passed automated checks but failed human review because motion was delayed, still visually mild, and not sufficiently scene-diverse.

v3 changes:

- camera motion starts at frame 0;
- camera motion ends at frame 80 for 81-frame clips;
- stronger template-aware camera variants;
- no dolly variants by default;
- per-trial scene seeds are tracked and no longer overridden by fixed non-drop template seeds;
- validator computes early motion and scene-hash metrics.

## Camera Mapping

| Template | Camera variants |
|---|---|
| drop | `orbit_left_32`, `orbit_right_32`, `orbit_left_36`, `orbit_right_36`, `strafe_left_065`, `strafe_right_065` |
| collision | `strafe_left_065`, `strafe_right_065`, `orbit_left_28`, `orbit_right_28` |
| roll | `strafe_left_065`, `strafe_right_065`, `orbit_left_26`, `orbit_right_26` |
| containment | `strafe_left_055`, `strafe_right_055`, `orbit_left_20`, `orbit_right_20`, `orbit_left_22`, `orbit_right_22` |

## Start0 Settings

- `camera_motion_start = 0`
- `camera_motion_end = 80`

## V3 Thresholds

- `target_visible_ratio >= 0.70`
- `max_invisible_frames <= 8`
- `camera_path_length_total >= 0.75`
- `camera_path_length_total <= 1.80`
- `camera_path_length_first_8_frames >= 0.08`
- `camera_path_length_first_16_frames >= 0.16`
- `background_motion_proxy_total >= 0.018`
- `background_motion_proxy_first_8_frames >= 0.006`

## Risks

- Stronger orbit/strafe may reject more samples as `too_extreme`.
- Start0 motion may expose framing problems earlier in the clip.
- If upstream templates still produce visually similar object layouts, scene-hash and human review must reject the batch.
