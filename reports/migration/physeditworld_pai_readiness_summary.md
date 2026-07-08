# PhysEditWorld PAI Readiness Preflight

Decision: `PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED`

## Checks

- `nas_mount`: `BLOCKED` (/mnt/workspace/hj/nas_hj)
  - blocker: path does not exist
  - next: mount or expose the PAI/NAS target path
- `physeditworld_root_candidates`: `BLOCKED` (reports/migration/physeditworld_candidates_raw.txt, rows=656)
  - blocker: no external-looking PhysEditWorld root candidate
  - next: provide/mount selected PhysEditWorld 50h root
- `strict_manifest`: `BLOCKED` (manifests/physeditworld_50h_all.jsonl, rows=0)
  - blocker: manifest has zero rows
  - next: mount selected PhysEditWorld 50h root and rerun audit/conversion
- `train_manifest`: `BLOCKED` (manifests/physeditworld_50h_train.jsonl, rows=0)
  - blocker: manifest has zero rows
  - next: mount selected PhysEditWorld 50h root and rerun audit/conversion
- `lingbot_train_manifest`: `BLOCKED` (manifests/physeditworld_50h_lingbot_train.jsonl, rows=0)
  - blocker: manifest has zero rows
  - next: mount selected PhysEditWorld 50h root and rerun audit/conversion
- `sample_schema`: `BLOCKED` (manifests/physeditworld_50h_all.jsonl, rows=0)
  - blocker: no sample row available
  - next: requires non-empty strict manifest

## Policy

This preflight is CPU/IO only. It does not launch rollout, training, DPO, StageB, GRPO, or checkpoint deletion.
It is intended to be rerun on H20 or PAI after the selected PhysEditWorld 50h root and NAS mount become visible.
