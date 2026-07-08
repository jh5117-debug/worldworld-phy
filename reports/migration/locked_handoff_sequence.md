# PhysEditWorld Locked Handoff Sequence

Decision: `LOCKED_HANDOFF_BLOCKED_AT_ROOT_SELECTION`

## Steps

- `root_selection`: `BLOCKED` / `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT`
  - command: `bash scripts/migration/select_physeditworld_root.sh`
  - evidence: `reports/migration/physeditworld_selected_root_status.json`
  - next: set PHYS_EDITWORLD_ROOTS to a strong selected PhysEditWorld 50h root

## Safety

This sequence is CPU/IO only. It locks a strong selected root before post-mount work, then refreshes Phase0, handoff, pipeline, and requirement reports.
It does not copy files, delete files, use GPUs, train, rollout, run DPO, or push large artifacts.
