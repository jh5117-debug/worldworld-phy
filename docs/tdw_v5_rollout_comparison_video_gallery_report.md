# TDW v5 Rollout Comparison Video Gallery Report

Date: 2026-06-12

## Purpose

The previous 12-condition rollout produced separate videos for Base, Stage A, and Stage B. That layout was hard to review because the reviewer had to open many files manually.

This update adds automatic three-panel comparison videos:

- left: Base
- middle: Stage A
- right: Stage B

Each panel has a top-left label burned into the video.

## Existing Gallery Updated

Rollout root:

`local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/12condition_base_stageA_stageB`

Comparison output:

`local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/12condition_base_stageA_stageB/comparison_videos/`

Generated:

- comparison videos: 12 / 12
- `comparison_summary.json`
- `comparison_index.md`
- `video_gallery.html`

## Code Update

New module:

`cam_physgeo/eval/make_rollout_comparison_videos.py`

Updated module:

`cam_physgeo/eval/rollout_compare_base_adapter.py`

Behavior:

- future rollout comparison runs can automatically create labeled side-by-side videos;
- existing rollout roots can be post-processed with:

```bash
python -m cam_physgeo.eval.make_rollout_comparison_videos \
  --rollout_root local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/12condition_base_stageA_stageB \
  --out_subdir comparison_videos \
  --variants "base:Base,stageA_adapter:Stage A,stageB_adapter:Stage B" \
  --panel_size 832x480 \
  --fps 16 \
  --overwrite true
```

Implementation detail:

- Uses ffmpeg when possible.
- Falls back to Python `imageio` + Pillow labeling when the available ffmpeg build lacks the `drawtext` filter.
