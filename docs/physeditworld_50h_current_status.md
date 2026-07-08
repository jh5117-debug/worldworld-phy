# PhysEditWorld 50h Current Status

Updated: 2026-07-08T17:29:56 CST

## Runtime State

- Host repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`.
- Branch: `physion-only-local-assets-videogpa-smoke`.
- Commit: `681b34f (HEAD -> physion-only-local-assets-videogpa-smoke, physion-only-cam-physgeo-dpo, main, cam-physgeo-dpo-refactor) Quiet TRD diagnostics and default empty paths`.
- H20 is expected to be reclaimed, so the first priority is migration preparation to PAI/NAS.
- Target NAS path: `/mnt/workspace/hj/nas_hj`.
- GPU policy for this line: physical GPU4, GPU5, GPU6, GPU7 only.
- Forbidden GPUs: physical GPU0, GPU1, GPU2, GPU3.
- Current observation: GPU4-7 are occupied by existing FastWAM/libero evaluation processes, so this update does not start training, rollout, or metrics jobs.

## Refocus

The project line is refocused away from old CSGO, old PhyInOne mixing, and direct large DPO. The current research line is PhysEditWorld-style LingBot-Fast physics-editable world model training.

PhysEditWorld must be treated as action + camera + gravity matched replay data, not as passive camera-only physics data. The first training stage uses PhysEditWorld 50h only. Our older passive physics data should be reserved for a later ablation after the PhysEditWorld-only baseline is understood.

## Gravity Conditioning

- First version: prompt-only gravity conditioning, matching the PhysEditWorld paper-style baseline.
- Prompt should include explicit text such as `The scene is rendered under gravity: 0.25g.`
- No gravity MLP is introduced in this version.
- No gravity embedding is introduced in this version.
- LingBot-Fast architecture is not changed for gravity in this version.

## Condition And Target

Condition:

- image or prefix video;
- prompt with gravity token;
- action trace;
- camera trajectory;
- intrinsics.

Target:

- future video under the same replay condition and gravity.

## This Round

This round is migration + data schema + baseline + gated warm-up preparation. It is not large DPO.

Allowed next phases:

1. H20 to PAI/NAS migration manifest and environment export.
2. PhysEditWorld 50h data audit and replay-group-safe splits.
3. LingBot-Fast input conversion with prompt-only gravity.
4. Original LingBot-Fast / base baseline rollout if GPU4-7 are free.
5. Rank32 support warm-up only after preflight and gates.
6. Anchored DPO pair construction only after warm-up video and metric gates.
7. Tiny anchored DPO probe only after pair gate.

## Explicit Non-Goals

- No large DPO.
- No train400.
- No StageB.
- No GRPO.
- No broad-LoRA.
- No full-data long StageA.
- No checkpoint, data, or weight deletion.
- No `local_assets`, videos, checkpoints, weights, or large logs pushed to Git.
- No GPU0-3 usage by this line.

## Source Context Files

Existing context files read/available:

- `README_cam_physgeo_dpo.md`
- `docs/project_refocus.md`
- `docs/experiment_plan.md`
- `docs/implementation_status.md`
- `docs/framework_completeness_audit.md`
- `docs/metrics.md`
- `docs/research_notes.md`
- `docs/data_locations.md`
- `docs/github_push_report.md`

Missing context files noted but not blocking:

- `docs/dpo_failure_root_cause_report.md`
- `docs/dpo_utility_calibration_v14_report.md`
- `docs/vjepa_videorepa_winner_anchor_plan.md`
- `docs/fulldata_lingbotfast_warmup_loser_eval_status.md`

## Initial Git Status Excerpt

```text
M .gitignore
 M configs/train_stage2_phycsgo_act.yaml
 D data/audit/csgo_human_eval_template.csv
 D data/audit/csgo_physics_taxonomy_v1.md
 D logs/.gitkeep
?? README_cam_physgeo_dpo.md
?? cam_physgeo/
?? configs/cam_physgeo/
?? configs/generated/
?? configs/train_stage1_physinone_cam.yaml.localbackup.20260428_063010
?? configs/train_stage2_phycsgo_act.runtime_act4.yaml
?? configs/train_stage2_phycsgo_act.yaml.bak_20260510_113145
?? docs/
?? eval_assets/
?? h20_probe_all_in_one.txt
?? h20_train_accel_probe_20260416_115015.txt
?? links/base_model
?? links/lingbot_code
?? links/stage1_epoch2
?? links/stage1_final
?? links/teacher_ckpt
?? links/videophy2_checkpoint
?? scripts/00_plan_local_assets.sh
?? scripts/00_readonly_audit.sh
?? scripts/01_build_data_manifest.sh
?? scripts/01_migrate_assets_to_project.sh
?? scripts/01_physion_download_or_check.sh
?? scripts/02_physion_hdf5_audit.sh
?? scripts/02_validate_data.sh
?? scripts/03_build_physion_manifest.sh
?? scripts/03_convert_cam_inputs.sh
?? scripts/04_convert_physion_cam_inputs.sh
?? scripts/04_reward_calibration.sh
?? scripts/05_reward_calibration.sh
?? scripts/05_stage1_warmup.sh
?? scripts/06_generate_rollouts.sh
?? scripts/06_stage1_physion_warmup.sh
?? scripts/07_build_dpo_pairs.sh
?? scripts/08_build_dpo_pairs.sh
?? scripts/08_export_videogpa_pairs.sh
?? scripts/08_stage2_anchored_dpo.sh
?? scripts/09_stage2_anchored_dpo.sh
?? scripts/09_stage3_self_dpo.sh
?? scripts/10_eval_all.sh
?? scripts/10_stage3_self_dpo.sh
?? scripts/11_eval_all.sh
?? scripts/12_generate_physion_movingcam_subset.sh
?? scripts/download_flux2_dev_devturbo_hf.sh
?? scripts/generate_videophy2_first_frames_flux2.py
?? scripts/safe_delete_from_manifest.sh
?? smoke_after_release_fix.txt
?? src/physical_consistency/stages/stage1_physinone_cam/trainer.py.bak_ddp_bundle_20260515_154317
?? tests/test_cam_physgeo_smoke.py
?? tests/test_physion_smoke.py
?? third_party/vjepa2_official/
```

## Phase 1 Data Audit Update (2026-07-08T18:05:23 CST)

Decision: `PHYS_EDIT_WORLD_DATA_NOT_FOUND`.

A bounded candidate-file audit was run from `reports/migration/physeditworld_candidates_raw.txt` rather than broad-scanning all legacy videos. The first 200 candidate paths produced 132 candidate rows but 0 strict OK rows for PhysEditWorld 50h training.

Evidence:

- Manifest: `manifests/physeditworld_50h_all.jsonl` has 0 rows.
- Splits: train/val/test and OOD manifests are present but empty.
- Audit CSV: `reports/physeditworld_50h/data_audit.csv` has 132 candidate rows.
- Summary: `reports/physeditworld_50h/data_audit_summary.md`.
- Main blockers: `MISSING_ACTION` and `MISSING_GRAVITY` after strict rejection of PhysInOne-style false positives.

No conversion, rollout, warm-up, pair construction, or DPO was run after this gate failure.

## Root Search And Phase 2 Update (2026-07-08T18:29:06 CST)

- Root search report: `reports/physeditworld_50h/root_search/root_search_summary.md`.
- Decision: `PHYS_EDIT_WORLD_ROOT_NOT_VISIBLE`.
- True PhysEditWorld selected 50h root is still not visible; repo self-generated files and PhysInOne legacy paths are rejected as false positives.
- Phase 2 conversion tooling is implemented and direct-smoke tested.
- Real conversion remains data-blocked because `manifests/physeditworld_50h_train.jsonl` has 0 rows.
- No GPU, rollout, warm-up, pair construction, or DPO was run.


## Phase 3/4 Readiness Update (2026-07-08T18:44:19 CST)

Decision: `PHASE3_PHASE4_SCAFFOLD_READY_DATA_BLOCKED`.

- Gravity metric helpers are implemented and direct-smoke tested.
- Baseline rollout wrapper is implemented and direct-smoke tested.
- Rank32 prompt-only gravity warm-up config exists and enforces GPU4-7 only.
- Future PhysEditWorld50-only vs PhysEditWorld50+our-physics50 ablation plan exists but is not run.
- Baseline result: `BASELINE_BLOCKED_EMPTY_MANIFEST` because `manifests/physeditworld_50h_lingbot_train.jsonl` has 0 rows.
- Test status: compileall PASS, direct smoke PASS, pytest unavailable; no pytest PASS is claimed.
- No GPU, rollout, warm-up, pair construction, or DPO was run.

Readiness report: `docs/physeditworld_50h_baseline_warmup_readiness_report.md`.


## PAI / Data Readiness Preflight Update (2026-07-08T19:00:08 CST)

Decision: `PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED`.

A CPU/IO-only readiness checker was added and run:

- Tool: `cam_physgeo/data/physeditworld_readiness.py`.
- Wrapper: `scripts/migration/check_physeditworld_pai_readiness.sh`.
- Checklist: `docs/physeditworld_50h_data_unblock_checklist.md`.
- CSV: `reports/migration/physeditworld_pai_readiness.csv`.
- JSON: `reports/migration/physeditworld_pai_readiness.json`.
- Summary: `reports/migration/physeditworld_pai_readiness_summary.md`.

Current blockers are explicit and machine-readable:

- NAS target `/mnt/workspace/hj/nas_hj` is not mounted/visible.
- No external-looking selected PhysEditWorld 50h root candidate is visible.
- `manifests/physeditworld_50h_all.jsonl`, train manifest, and LingBot train manifest all have 0 rows.

Test status: compileall PASS, direct readiness smoke PASS, pytest unavailable; no pytest PASS is claimed. No GPU, rollout, warm-up, pair construction, or DPO was run.


## Phase 4/6 Gate Scaffold Update (2026-07-08T19:06:16 CST)

Decision: `WARMUP_BLOCKED_EMPTY_MANIFEST` and `PAIR_BUILDER_BLOCKED_WARMUP_GATE`.

New safety-gated entry points were added:

- Warm-up gate: `cam_physgeo/training/train_physeditworld_warmup.py`.
- Anchored pair gate: `cam_physgeo/dpo/physeditworld_pair_builder.py`.
- Tests: `tests/test_physeditworld_warmup_trainer.py`, `tests/test_physeditworld_pair_builder.py`.

Smoke evidence:

- Warm-up preflight report: `reports/physeditworld_50h_warmup_rank32/preflight.csv`.
- Warm-up preflight summary: `reports/physeditworld_50h_warmup_rank32/preflight_summary.md`.
- Pair gate audit: `reports/physeditworld_dpo_pairs_anchored_v0/pair_audit.csv`.
- Pair gate summary: `reports/physeditworld_dpo_pairs_anchored_v0/pair_summary.md`.

The warm-up command was invoked with `CUDA_VISIBLE_DEVICES=4`, which passes the GPU4-7 policy, but it correctly refused to train because `manifests/physeditworld_50h_lingbot_train.jsonl` has 0 rows. The pair builder correctly emitted an empty anchored-pair manifest because no warm-up checkpoint has passed video/metric/Codex audit.

Test status: compileall PASS, direct Phase 4/6 smoke PASS, pytest unavailable; no pytest PASS is claimed. No rollout, no training, no pair admission, and no DPO was run.


## Phase 5/7 Gate Scaffold Update (2026-07-08T19:13:39 CST)

Decision: `CHECKPOINT_EVAL_BLOCKED_EVAL_MANIFEST_MISSING` and `TINY_DPO_BLOCKED_INSUFFICIENT_PAIRS`.

New safety-gated entry points were added:

- Checkpoint eval gate: `cam_physgeo/eval/physeditworld_checkpoint_eval.py`.
- Tiny anchored DPO gate: `cam_physgeo/dpo/physeditworld_tiny_dpo_probe.py`.
- Tests: `tests/test_physeditworld_checkpoint_eval.py`, `tests/test_physeditworld_tiny_dpo_probe.py`.

Smoke evidence:

- Checkpoint eval summary: `reports/physeditworld_50h_warmup_rank32/checkpoint_eval_gate_summary.md`.
- Gravity metrics placeholder: `reports/physeditworld_50h_warmup_rank32/gravity_metrics.csv`.
- Video audit placeholder: `reports/physeditworld_50h_warmup_rank32/video_audit.csv`.
- Tiny DPO gate summary: `reports/physeditworld_tiny_dpo_v0/tiny_dpo_gate_summary.md`.
- Tiny DPO decision: `reports/physeditworld_tiny_dpo_v0/best_checkpoint_decision.json`.

The checkpoint eval gate was invoked with `CUDA_VISIBLE_DEVICES=4`, which passes the GPU4-7 policy, but it correctly refused to evaluate because `manifests/physeditworld_50h_lingbot_val.jsonl` is missing. The tiny DPO gate also used `CUDA_VISIBLE_DEVICES=4` and correctly refused to train because the anchored pair manifest has 0 rows, below the 100-pair gate.

Test status: compileall PASS, direct Phase 5/7 smoke PASS, pytest unavailable; no pytest PASS is claimed. No rollout, no metrics scoring, no visual audit, no training, and no DPO was run.


## Pipeline Gate Orchestrator Update (2026-07-08T19:18:47 CST)

Decision: `PIPELINE_BLOCKED_AT_READINESS`.

A safe phase-gate orchestrator was added:

- Orchestrator: `cam_physgeo/orchestration/physeditworld_pipeline_gate.py`.
- Launch script: `scripts/run_physeditworld_pipeline_gates.sh`.
- Test: `tests/test_physeditworld_pipeline_gate.py`.
- CSV: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.csv`.
- JSON: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json`.
- Summary: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md`.

The orchestrator reruns/reads readiness first and stops before baseline, warm-up, checkpoint eval, pair construction, or tiny DPO when prerequisites are blocked. Current stop point is readiness because NAS and the selected PhysEditWorld 50h root are not visible and the strict/LingBot manifests are empty.

Test status: compileall PASS, direct pipeline gate smoke PASS, pytest unavailable; no pytest PASS is claimed. No GPU, rollout, metrics scoring, visual audit, training, or DPO was run.


## PAI Bootstrap And Requirement Matrix Update (2026-07-08T19:27:35 CST)

Decision: `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS`.

Added PAI recovery and requirement-audit artifacts:

- PAI bootstrap script: `scripts/migration/bootstrap_pai_physeditworld.sh`.
- Bootstrap doc: `docs/physeditworld_50h_pai_bootstrap.md`.
- Requirement matrix generator: `cam_physgeo/orchestration/physeditworld_requirement_matrix.py`.
- Test: `tests/test_physeditworld_requirement_matrix.py`.
- Matrix CSV/JSON/MD: `reports/physeditworld_50h/requirement_matrix.*`.

Current matrix: 19 requirements total, 11 PASS, 7 BLOCKED, 1 MISSING. The earliest blocker remains migration/data readiness: NAS and selected PhysEditWorld 50h root are not visible.

Test status: compileall PASS, direct requirement-matrix smoke PASS, pytest unavailable; no pytest PASS is claimed. No GPU, rollout, metrics scoring, visual audit, training, or DPO was run.


## Post-Mount Continuation Update (2026-07-08T19:34:47 CST)

Decision: `POST_MOUNT_BLOCKED_AT_ROOT_INPUT`.

Added a safe continuation entry point for the moment the selected PhysEditWorld 50h root becomes visible:

- Tool: `cam_physgeo/orchestration/physeditworld_post_mount.py`.
- Launch script: `scripts/continue_physeditworld_after_mount.sh`.
- Doc: `docs/physeditworld_50h_post_mount_continue.md`.
- Test: `tests/test_physeditworld_post_mount.py`.
- Status CSV/JSON/MD: `reports/physeditworld_50h/post_mount/post_mount_status.*` and `post_mount_summary.md`.

Usage after mount:

```bash
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h \
bash scripts/continue_physeditworld_after_mount.sh
```

With no root provided, the smoke correctly blocks at root input. The continuation does not start warm-up training, checkpoint rollout, DPO, StageB, GRPO, broad-LoRA, deletion, or large-file push.

Test status: compileall PASS, direct post-mount smoke PASS, pytest unavailable; no pytest PASS is claimed.

## Migration Asset Validation Update (2026-07-08T19:58:00 CST)

Decision: MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.

A read-only migration asset validator was added and run before any H20 to PAI/NAS copy:

- Tool: cam_physgeo/orchestration/migration_asset_validator.py.
- Wrapper: scripts/migration/validate_physeditworld_migration_assets.sh.
- Doc: docs/physeditworld_50h_migration_asset_validation.md.
- CSV: reports/migration/migration_asset_validation.csv.
- JSON: reports/migration/migration_asset_validation.json.
- Summary: reports/migration/migration_asset_validation_summary.md.

Validation evidence:

- Manifest rows checked: 800 total, 300 weights rows and 500 data rows.
- Present file bytes counted: 5.97 GB.
- Execute script guard: PASS; MIGRATION_APPROVED=1 is required.
- NAS target /mnt/workspace/hj/nas_hj: BLOCKED_MISSING.
- Safety: no files copied, no files deleted, no large directory recursive hashing, no local_assets payload.

This confirms migration execution is still blocked on the NAS mount/visibility, not on the validator itself. No GPU, rollout, warm-up, pair construction, or DPO was run.

## Requirement Matrix Asset-Validation Update (2026-07-08T20:06:00 CST)

Decision remains: PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS.

The requirement matrix now includes migration asset validation as an explicit Phase 0 gate:

- Requirement count: 20.
- Status counts: PASS=11, BLOCKED=8, MISSING=1.
- New Phase 0 row: migration asset validation = BLOCKED.
- Evidence: reports/migration/migration_asset_validation.json.
- Detail: decision=MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.

This makes the current migration blocker sharper: both PAI/NAS data readiness and migration asset validation are blocked until /mnt/workspace/hj/nas_hj and the selected PhysEditWorld 50h root are visible. No training, rollout, metric scoring, pair construction, or DPO was run.

## Pipeline Gate Asset-Validation Update (2026-07-08T20:12:00 CST)

Decision remains: PIPELINE_BLOCKED_AT_READINESS.

The safe pipeline gate now reads both Phase 0 readiness and migration asset validation before any baseline, warm-up, pair construction, or tiny DPO step:

- readiness: PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED.
- asset_validation: MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.
- Pipeline phases reported: 2.
- Summary: reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md.

This keeps the live pipeline gate aligned with the requirement matrix: the selected PhysEditWorld 50h root and /mnt/workspace/hj/nas_hj must be visible before any copy, rollout, warm-up, or DPO can proceed. No GPU, rollout, metric scoring, visual audit, training, or DPO was run.

## Migration Copy Plan Template Update (2026-07-08T20:22:00 CST)

Decision: COPY_PLAN_REVIEW_REQUIRED.

An explicit migration copy-plan template was generated from the weight/data candidate manifests:

- Tool: cam_physgeo/orchestration/migration_copy_plan.py.
- Wrapper: scripts/migration/build_physeditworld_migration_copy_plan.sh.
- TSV: reports/migration/approved_copy_manifest_template.tsv.
- JSON: reports/migration/approved_copy_manifest_template.json.
- Summary: reports/migration/approved_copy_manifest_template_summary.md.

Validation evidence:

- Rows: 800 total, 300 weights rows and 500 data rows.
- Approved rows: 0.
- Every row defaults to approved=false.
- Copy statuses: NEEDS_REVIEW_FILE=561, NEEDS_REVIEW_DIR=237, BLOCKED_MISSING_ON_H20=2.
- Safety: no data, weights, checkpoints, local_assets, or videos were copied; no files were deleted.

This prevents accidental broad migration from the noisy candidate manifests. After NAS and the selected PhysEditWorld 50h root are visible, only rows confirmed as necessary for restore should be changed to approved=true.

## Approved-Only Migration Copy Executor Update (2026-07-08T20:34:00 CST)

Decision: APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS.

A guarded executor was added for future migration copies:

- Tool: cam_physgeo/orchestration/migration_approved_copy.py.
- Wrapper: scripts/migration/run_approved_migration_copy.sh.
- CSV: reports/migration/approved_copy_status.csv.
- JSON: reports/migration/approved_copy_status.json.
- Summary: reports/migration/approved_copy_status_summary.md.

Current evidence:

- Approved rows considered: 0.
- Execute mode: false.
- local_assets payloads are rejected.
- No files were copied or deleted.
- To execute in the future, rows must first be changed to approved=true and the command must be run with MIGRATION_APPROVED=1 and MIGRATION_COPY_APPROVED=1 plus --execute.

This closes the migration safety loop: candidate manifests produce a review template, the review template defaults to no approvals, and the executor refuses to copy until explicit approvals exist.

## Pipeline Gate Approved-Copy Update (2026-07-08T20:40:00 CST)

Decision remains: PIPELINE_BLOCKED_AT_READINESS.

The safe pipeline gate now reads three Phase 0 migration states before any baseline, warm-up, pair construction, or tiny DPO step:

- readiness: PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED.
- asset_validation: MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.
- approved_copy: APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS.
- Pipeline phases reported: 3.
- Summary: reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md.

This aligns the live pipeline gate with the full migration safety chain. No copy, GPU use, rollout, metric scoring, visual audit, training, or DPO was run.

## Phase 0 Migration Preflight Update (2026-07-08T20:46:00 CST)

Decision: PHYS_EDITWORLD_PHASE0_BLOCKED_AT_READINESS.

A consolidated Phase 0 preflight was added. It reruns and summarizes all safe migration gates without copying assets or using GPU:

- Tool: cam_physgeo/orchestration/physeditworld_phase0_preflight.py.
- Wrapper: scripts/migration/run_physeditworld_phase0_preflight.sh.
- CSV: reports/migration/phase0_preflight_status.csv.
- JSON: reports/migration/phase0_preflight_status.json.
- Summary: reports/migration/phase0_preflight_summary.md.

The current preflight has 6 steps:

1. PAI/NAS/data readiness: PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED.
2. Migration asset validation: MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.
3. Copy-plan template: COPY_PLAN_REVIEW_REQUIRED.
4. Approved-only copy status: APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS.
5. Requirement matrix: PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS.
6. Pipeline gate: PIPELINE_BLOCKED_AT_READINESS.

Safety: the preflight does not run rsync execute, does not pass --execute to the approved-copy tool, does not copy data/weights/checkpoints/videos/local_assets, does not delete files, and does not use GPUs.

