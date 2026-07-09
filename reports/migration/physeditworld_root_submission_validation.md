# PhysEditWorld Root Submission Validation

Decision: `PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE`

## Status Counts

- `WAITING_FOR_FILLED_TEMPLATE`: 1

## Rows

- row `1`: `WAITING_FOR_FILLED_TEMPLATE` root=`<absolute path to selected PhysEditWorld 50h root>`
  - missing fields: `candidate_root;video_or_frames_glob;action_trace_glob;camera_trajectory_or_poses_glob;intrinsics_glob;gravity_label_or_metadata_glob;replay_group_or_matched_replay_glob`
  - next: fill candidate_root plus action/camera/intrinsics/gravity/replay/video globs

## Safety

This validator is CPU/IO only. It reads the filled TSV and bounded non-recursive evidence globs. It does not copy files, delete files, approve migration rows, select/lock a root, use GPUs, train, rollout, evaluate videos, or run DPO.
