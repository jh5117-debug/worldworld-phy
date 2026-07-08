# PhysEditWorld Pipeline Gate Summary

Decision: `PIPELINE_BLOCKED_AT_ROOT_SCHEMA_PROBE`

## Phases

- `manifest_init`: `PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT` from `reports/physeditworld_50h/manifest_init/empty_manifest_init.json`
  - next: check selected-root schema probe
- `root_schema_probe`: `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT` from `reports/migration/physeditworld_root_schema_probe.json`
  - next: set PHYS_EDITWORLD_ROOTS to a selected root with action/camera/intrinsics/gravity/replay/video evidence

## Safety

This orchestrator is a gate collector. It does not launch large DPO, train400, StageB, GRPO, broad-LoRA, checkpoint deletion, or any local_assets push.
When prerequisites are blocked it stops before rollout, warm-up, pair construction, and tiny DPO.
