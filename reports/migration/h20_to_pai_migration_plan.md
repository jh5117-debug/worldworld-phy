# H20 To PAI/NAS Migration Plan For PhysEditWorld Run

Generated: 2026-07-08T17:38:13 CST

## Target

- Target NAS path: `/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708`.
- Current df output:

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme2n1p1  3.4T  3.1T  382G  90% /home/nvme03
/dev/nvme3n1p1  3.4T  3.1T  345G  91% /home/nvme04
```

If `/mnt/workspace/hj/nas_hj` is absent from the df output, migration execute is `CONNECTIVITY_OR_MOUNT_BLOCKED` until the mount is available.

## Restore Code

1. Clone/pull `git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git`.
2. Checkout branch `physion-only-local-assets-videogpa-smoke` or the later migration branch containing this PRD.
3. Use `reports/migration/git_log_30.txt` and `git_status_short.txt` to inspect local divergence.

## Restore Environment

- Conda export: `reports/migration/environment_no_builds.yml`.
- Pip freeze: `reports/migration/pip_freeze.txt`.
- Python: `reports/migration/python_version.txt`, `python_path.txt`.
- CUDA/Torch: `reports/migration/torch_cuda_info.txt`, `nvidia_smi.txt`.

## Weights

- Candidate manifest: `reports/migration/required_weights_manifest.tsv` (300 rows).
- SHA status: `reports/migration/required_weights_sha256.txt`.
- Do not migrate all old failed checkpoints or full `local_assets`.
- Large files are marked for deferred checksum to avoid an IO storm during this planning pass.

## Data

- Candidate manifest: `reports/migration/required_data_manifest.tsv` (500 rows).
- PhysEditWorld raw candidates: `reports/migration/physeditworld_candidates_raw.txt`.
- Phase 1 must still build a strict `physeditworld_50h_all.jsonl` with action/camera/intrinsics/gravity/replay-group validation.

## Not Migrated By Default

- Full `local_assets/`.
- Old rollout videos.
- Old contact sheets.
- Failed checkpoints.
- Raw generated videos not needed for PhysEditWorld restore.

## Dry Run

Run:

```bash
bash scripts/migration/rsync_h20_to_pai_dryrun.sh
```

## Execute Guard

Execution requires:

```bash
MIGRATION_APPROVED=1 bash scripts/migration/rsync_h20_to_pai_execute.sh
```

The execute script currently copies only code/docs/reports/scripts. Weight/data copy remains manifest-review-gated.

## Current Decision

- Migration preparation: `MIGRATION_MANIFEST_PREPARED`.
- Copy execution: `NOT_RUN`.
- Training: `NOT_RUN`.
- GPU usage: none for this migration audit.


## Readiness Preflight Update (2026-07-08T19:00:08 CST)

Run:

```bash
bash scripts/migration/check_physeditworld_pai_readiness.sh
```

Latest decision: `PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED`.

This confirms migration execution and Phase 3 rollout are still blocked until the NAS target and selected PhysEditWorld 50h root are visible. The checker is CPU/IO-only and safe to rerun on H20 or PAI.
