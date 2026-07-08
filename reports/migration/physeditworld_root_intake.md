# PhysEditWorld Root Intake Handoff

Decision: `PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT`

## Required External Input

Provide the real PhysEditWorld selected 50h root and expose it on H20/PAI as a directory containing structural evidence:

- action trace files
- camera trajectory / poses
- intrinsics / calibration
- gravity labels
- replay-group or matched-replay metadata
- target videos / frames

Do not provide VideoPHY/Wan result folders, model checkpoints, old PhysInOne conditions, contact sheets, or prompt-derived MP4 folders as the selected root.

## Current Checks

- `root_candidates`: `BLOCKED` / `PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG`
  - path: `reports/migration/physeditworld_root_candidates_ranked.json`
  - detail: no automatically usable PhysEditWorld selected-50h root is visible
  - next: mount/provide the real selected 50h root and set PHYS_EDITWORLD_ROOTS
- `root_input`: `BLOCKED` / `ROOTS_MISSING_OR_UNSET`
  - detail: roots=0
  - next: export PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h
- `root_selection_lock`: `BLOCKED` / `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT`
  - path: `reports/migration/physeditworld_selected_root_status.json`
  - detail: root lock not written
  - next: PHYS_EDITWORLD_ROOTS=/path/to/root bash scripts/migration/select_physeditworld_root.sh
- `locked_handoff`: `BLOCKED` / `LOCKED_HANDOFF_BLOCKED_AT_ROOT_SELECTION`
  - path: `reports/migration/locked_handoff_sequence.json`
  - detail: safe locked handoff is not complete
  - next: PHYS_EDITWORLD_ROOTS=/path/to/root bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
- `pai_handoff`: `BLOCKED` / `PAI_HANDOFF_BLOCKED_NAS_OR_ROOT`
  - path: `reports/migration/pai_handoff_status.json`
  - detail: NAS/root/manifests not all ready
  - next: mount NAS/root and rerun verify_pai_physeditworld_handoff.sh
- `strict_manifest_rows`: `BLOCKED` / `STRICT_ROWS_EMPTY`
  - path: `manifests/physeditworld_50h_all.jsonl;manifests/physeditworld_50h_train.jsonl`
  - detail: all=0 train=0
  - next: run manifest audit and replay-group split after root lock
- `lingbot_train_rows`: `BLOCKED` / `LINGBOT_ROWS_EMPTY`
  - path: `manifests/physeditworld_50h_lingbot_train.jsonl`
  - detail: rows=0
  - next: run prompt-only gravity conversion after strict split
- `completion_audit`: `BLOCKED` / `PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION`
  - path: `reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json`
  - detail: objective remains incomplete
  - next: bash scripts/migration/run_physeditworld_completion_audit.sh

## Safe Resume Commands

```bash
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys
export PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h
bash scripts/migration/select_physeditworld_root.sh
PHYS_EDITWORLD_ROOTS=$PHYS_EDITWORLD_ROOTS bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
bash scripts/migration/run_physeditworld_completion_audit.sh
```

## Safety

This intake report is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, evaluate videos, or run DPO.
