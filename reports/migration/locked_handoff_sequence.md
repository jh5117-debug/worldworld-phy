# PhysEditWorld Locked Handoff Sequence

Decision: `LOCKED_HANDOFF_BLOCKED_AT_ROOT_SCHEMA_PROBE`

## Steps

- `empty_manifest_init`: `PASS` / `PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT`
  - command: `bash scripts/migration/init_physeditworld_empty_manifests.sh`
  - evidence: `reports/physeditworld_50h/manifest_init/empty_manifest_init.json`
- `root_schema_probe`: `BLOCKED` / `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT`
  - command: `bash scripts/migration/probe_physeditworld_root_schema.sh`
  - evidence: `reports/migration/physeditworld_root_schema_probe.json`
  - next: set PHYS_EDITWORLD_ROOTS to a root with action/camera/intrinsics/gravity/replay/video evidence

## Safety

This sequence is CPU/IO only. It locks a strong selected root before post-mount work, then refreshes Phase0, handoff, pipeline, and requirement reports.
It does not copy files, delete files, use GPUs, train, rollout, run DPO, or push large artifacts.
