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
