# Cleanup Plan

No cleanup has been executed. The safe sequence is:

1. Review `cleanup/protected_manifest.tsv` and keep all protected roots.
2. Review `cleanup/candidate_delete_manifest.tsv` by risk level.
3. For low risk only, reply exactly `确认删除 low risk` before any deletion run.
4. For medium/high risk, reply with exact manifest paths or an edited manifest. Checkpoints, datasets, weights, HDF5, MP4, and physical data remain high risk.
5. Only after confirmation, run `scripts/safe_delete_from_manifest.sh --dry-run` with `CLEANUP_APPROVED=1` to print paths and sizes again.
6. Then run without `--dry-run` only if the dry-run output matches the approved list.

The safe delete script refuses to run unless `CLEANUP_APPROVED=1`, skips protected patterns, logs to `cleanup/delete_log_时间.txt`, and does not delete anything outside the manifest.

Estimated reclaim if all candidates were approved: about 1.34T, dominated by the deprecated processed game/action data and five large old checkpoints. This is only a planning number, not an action.
