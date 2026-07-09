# PhysEditWorld Root Submission Template

Decision: `PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY`

## Purpose

This template is the external/PAI handoff form for the real PhysEditWorld selected 50h root. It does not select a root and it does not fabricate data. Fill one row per candidate root before rerunning the selected-root/schema gates.

## Template File

- TSV: `reports/migration/physeditworld_root_submission_template.tsv`

## Required Evidence

- `video_or_frames_glob`
- `action_trace_glob`
- `camera_trajectory_or_poses_glob`
- `intrinsics_glob`
- `gravity_label_or_metadata_glob`
- `replay_group_or_matched_replay_glob`

A valid first-root candidate must expose action traces, camera trajectory or poses, intrinsics/calibration, explicit gravity labels or metadata, replay-group or matched-replay metadata, and target videos or frames. Prompt/text metadata and split/scene manifests are strongly recommended when present.

Do not point this template at Physion, PhyInOne, VideoPHY, Wan/LingBot rollout outputs, contact sheets, local_assets experiment folders, checkpoint folders, or prompt-derived MP4 folders. Those are not the selected PhysEditWorld 50h root.

## Review Status Values

- `PENDING_EXTERNAL_INPUT`
- `READY_FOR_SCHEMA_PROBE`
- `REJECTED_NOT_PHYS_EDIT_WORLD`
- `REJECTED_INCOMPLETE_EVIDENCE`

## Safe Resume Commands After Filling

```bash
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys
export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
bash scripts/migration/select_physeditworld_root.sh
bash scripts/migration/probe_physeditworld_root_schema.sh
bash scripts/migration/prepare_physeditworld_root_intake.sh
bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
```

## Safety

This generator is CPU/IO only. It does not scan candidate roots recursively, copy files, delete files, approve migration rows, use GPUs, train, rollout, evaluate videos, or run DPO.
