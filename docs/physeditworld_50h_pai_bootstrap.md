# PhysEditWorld 50h PAI Bootstrap

This document describes the lightweight recovery path on PAI/NAS after H20 is reclaimed.

## Bootstrap Command

```bash
PAI_ROOT=/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708/code \
REPO_URL=git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git \
BRANCH=physion-only-local-assets-videogpa-smoke \
bash scripts/migration/bootstrap_pai_physeditworld.sh
```

The script clones or updates the repo, checks out the PhysEditWorld branch, writes a PAI restore packet, runs handoff verification, Phase0 preflight, backend readiness, the safe pipeline gate, the requirement matrix, the completion audit, then refreshes restore/handoff/restore once more so the two reports reference the newest evidence.

## What It Does Not Do

- It does not copy large data or weights by itself.
- It does not run training, rollout, DPO, StageB, GRPO, or broad-LoRA.
- It does not delete checkpoints, data, or weights.
- It does not push videos, images, checkpoints, or `local_assets`.

## Expected Current Decision

Until the selected PhysEditWorld 50h root and NAS target are visible, the expected decision is:

```text
PIPELINE_BLOCKED_AT_ROOT_SCHEMA_PROBE
```

Current H20 blockers before NAS/root are visible should include:

```text
PAI_HANDOFF_BLOCKED_NAS_OR_ROOT
PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY
PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_CANDIDATES
PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION
```

The required next action is to mount/provide the selected PhysEditWorld 50h root, then rerun the bootstrap or:

```bash
export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness
bash scripts/run_physeditworld_pipeline_gates.sh
python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix
bash scripts/migration/run_physeditworld_completion_audit.sh
bash scripts/migration/run_physeditworld_pai_restore_packet.sh
bash scripts/migration/write_physeditworld_external_unblock_packet.sh
bash scripts/migration/verify_pai_physeditworld_handoff.sh
bash scripts/migration/run_physeditworld_pai_restore_packet.sh
```


## Handoff Verification Command

After cloning/updating the repo on PAI or after a NAS/root mount change, run:

```bash
bash scripts/migration/verify_pai_physeditworld_handoff.sh
```

Expected current H20 decision before NAS/root is visible:

```text
PAI_HANDOFF_BLOCKED_NAS_OR_ROOT
```

Once the selected PhysEditWorld 50h root is available, rerun with:

```bash
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h   bash scripts/migration/verify_pai_physeditworld_handoff.sh
```

The verifier is read-only and does not copy data, launch training/rollout/eval, use GPUs, delete files, or push large artifacts.


## Selected Root Lock Command

Before running the post-mount continuation, validate and lock the selected PhysEditWorld 50h root:

```bash
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h   bash scripts/migration/select_physeditworld_root.sh
```

Only `PHYS_EDITWORLD_ROOT_SELECTION_LOCKED` should be treated as safe to continue into manifest audit. Weak candidates require manual review and should not be used for training/rollout.
