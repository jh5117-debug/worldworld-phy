# PhysEditWorld 50h Data Audit Report

Updated: 2026-07-08T18:05:23 CST

Decision: `PHYS_EDIT_WORLD_DATA_NOT_FOUND`

## Inputs

- Candidate source: `reports/migration/physeditworld_candidates_raw.txt`.
- Audit mode: candidate-file bounded audit with `--max_candidates 200 --skip_video_probe`.
- GPU use: none.

## Outputs

- `manifests/physeditworld_50h_all.jsonl`: 0 rows.
- `manifests/physeditworld_50h_train.jsonl`: 0 rows.
- `manifests/physeditworld_50h_val.jsonl`: 0 rows.
- `manifests/physeditworld_50h_test.jsonl`: 0 rows.
- `reports/physeditworld_50h/data_audit.csv`: 132 candidate rows.
- `reports/physeditworld_50h/data_audit_summary.md`: decision summary.
- `reports/physeditworld_50h/replay_group_leakage_check.csv`: header-only because no strict OK rows.

## Result

The bounded search found files whose names contain gravity/action/replay-style tokens, but none satisfied the strict Phase 1 schema for training. Candidate rows were rejected primarily as `MISSING_ACTION` or `MISSING_GRAVITY` after strict rejection of PhysInOne-style false positives.

Some gravity labels such as `77g` and `151g` are likely false positives from filename numbers rather than real PhysEditWorld gravity values. This reinforces that the real selected 50h PhysEditWorld root must be located explicitly before training.

## Gate

Phase 2 LingBot conversion, baseline rollout, rank32 warm-up, anchored pair construction, and tiny DPO remain blocked until a valid PhysEditWorld 50h manifest exists.

## Tests

- `python3 -m compileall` on the new Phase 1 modules/tests: PASS.
- Direct import/smoke: PASS via `reports/physeditworld_50h/test_logs/direct_phase1_smoke.log`.
- `pytest`: not available in the active shell; no pytest PASS is claimed.
