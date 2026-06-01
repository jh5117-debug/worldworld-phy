# Prior Art: Physion / TDW Generation

## Local Sources Found

Official / upstream code is present locally:

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021`
- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/tdw_physics`
- `local_assets/third_party/physion_official_repo`

Existing moving-camera project assets are present under:

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505`
- `local_assets/data/physion/`

External primary references checked:

- https://github.com/cogtoolslab/physics-benchmarking-neurips2021
- https://github.com/threedworld-mit/tdw
- https://threedworld.org/

## Relationship Between Physion and TDW

The official Physion repository is primarily a benchmark/reproduction repo and
assumes stimuli have been generated with `tdw_physics`. The generation stack is
therefore:

1. TDW / ThreeDWorld runtime and Python controller.
2. `tdw_physics` scenario generation code.
3. Physion benchmark organization and metadata.
4. This project's moving-camera extensions and conversion into LingBot camera
   inputs.

Do not assume official Physion contains large moving-camera data. The
moving-camera logic is a project extension layered on TDW/tdw_physics outputs.

## Existing Moving-Camera Chain

The local moving-camera tree contains:

- generated output folders such as `current_gt_physion_relative_yaw180_*`;
- smoke outputs such as `smoke_physion_pilot_*`;
- TDW/Physion assets under `assets/tdw_asset_bundles`;
- local conda env `.conda_envs/tdw-physion`;
- wrappers and generated outputs that include camera motions, HDF5, depth, ID,
  camera matrices, and converted LingBot inputs.

The existing project conversion chain already proved it can produce:

- RGB video / target mp4;
- HDF5-backed clean metadata;
- depth and ID masks for clean GT;
- poses and projection matrices;
- converted `[fx, fy, cx, cy]` intrinsics for LingBot;
- prompts and `use_action=false` metadata.

## Generation Risks

- TDW runtime and Unity build dependencies can be brittle.
- Physion official static/test stimuli are not equivalent to our moving-camera
  clips.
- HDF5 key names and camera matrix conventions must be audited per template.
- Large generation can consume substantial disk; never write into old raw data
  folders.
- Camera motion distributions must be balanced, not only exaggerated stress
  motions.

## Small-Scale Plan Before Any Large Generation

No generation was run in this round. Future generation should be staged:

1. one-sample dry-run with a new output root;
2. 10-sample smoke across two or three templates;
3. 50-sample validation with HDF5/key/contact-sheet audit;
4. 200-sample pilot with reward and camera-stress stats;
5. 1k+ batch only after storage/runtime approval.

Outputs should go under:

`local_assets/data/physion/generated_v2/`

Large-scale generation should not start until the user confirms storage, clip
count, template list, camera motions, and TDW runtime allocation.
