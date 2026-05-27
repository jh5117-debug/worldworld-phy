# Physion Moving-Camera Generation Plan

If official Physion HDF5 lacks camera metadata, regenerate a small TDW/Physion subset with:

- RGB
- depth
- ID mask
- camera_position
- camera_aim
- camera_pose
- projection/intrinsics
- object states
- event metadata
- prompt metadata

Generation must write to a new timestamped output directory and never overwrite existing Physion moving-camera data.

First allowed run: dry-run plus 1-3 samples only.
