# PhysEditWorld 50h PAI Bootstrap

This document describes the lightweight recovery path on PAI/NAS after H20 is reclaimed.

## Bootstrap Command

```bash
PAI_ROOT=/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708/code \
REPO_URL=git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git \
BRANCH=physion-only-local-assets-videogpa-smoke \
bash scripts/migration/bootstrap_pai_physeditworld.sh
```

The script clones or updates the repo, checks out the PhysEditWorld branch, runs the safe pipeline gate, and regenerates the requirement matrix.

## What It Does Not Do

- It does not copy large data or weights by itself.
- It does not run training, rollout, DPO, StageB, GRPO, or broad-LoRA.
- It does not delete checkpoints, data, or weights.
- It does not push videos, images, checkpoints, or `local_assets`.

## Expected Current Decision

Until the selected PhysEditWorld 50h root and NAS target are visible, the expected decision is:

```text
PIPELINE_BLOCKED_AT_READINESS
```

The required next action is to mount/provide the selected PhysEditWorld 50h root, then rerun the bootstrap or:

```bash
bash scripts/run_physeditworld_pipeline_gates.sh
python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix
```
