# TDW v2 Visible-Motion Profile Report

Date: 2026-06-05

## New Profile

Added:

`warmup_visible_motion`

Purpose:

Generate Physion-style TDW moving-camera clips whose camera motion is obvious to a human viewer, while remaining non-stress and suitable for later LingBot-Fast camera-conditioned warmup.

## Variants

| Variant | Intended effect |
|---|---|
| `orbit_left_24` | visible left orbit, non-reobserve |
| `orbit_right_24` | visible right orbit, non-reobserve |
| `orbit_left_28` | stronger left orbit, still below stress |
| `orbit_right_28` | stronger right orbit, still below stress |
| `strafe_left_050` | visible lateral camera motion |
| `strafe_right_050` | visible lateral camera motion |
| `dolly_in_025` | visible dolly-in |
| `dolly_out_025` | visible dolly-out |

## Comparison With `warmup_mild`

| Motion type | `warmup_mild` | `warmup_visible_motion` |
|---|---:|---:|
| orbit | 12 degrees | 24 / 28 degrees |
| strafe | 0.25 | 0.50 |
| dolly | 0.10 | 0.25 |

## Banned Motions

The new profile still bans:

- lookaway
- offscreen
- `relative_yaw_180`
- reobserve
- occluder-driven view loss
- extreme camera motion

## Validation Thresholds

New visible-motion thresholds:

- `target_visible_ratio >= 0.75`
- `max_invisible_frames <= 8`
- `min_camera_path_length >= 0.45`
- `max_camera_path_length <= 1.50`
- `min_background_motion_proxy >= 0.012`
- `min_video_motion_proxy >= 0.015`

## Expected Behavior

This profile should produce clips where:

- the teacher can see camera motion from contact sheets or videos;
- background parallax is visible;
- foreground remains visible most of the time;
- clips are not stress/reobserve examples.

Remaining risk:

Some physics templates can move foreground objects toward the frame edge. The validator therefore rejects clips that are too extreme or lose the target for too long.
