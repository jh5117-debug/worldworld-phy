# Reward Calibration Report

- smoke rows: 36
- comparisons: 33
- clean_gt_win_rate on default smoke order: 0.0

WARNING: the first smoke rows were HDF5-only moving-camera samples without decoded MP4 previews, so the lightweight video proxy rewards could not separate clean and corrupted records. This is expected for fast manifest rows with `needs_video_preview_or_decode`.

Next calibration run should use rows with `video_path` present or materialize moving-camera MP4 previews, then enable RAFT/depth/DINO backends.
