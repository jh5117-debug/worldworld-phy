# PhysEditWorld Requirement Matrix

Decision: `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS`

## Status Counts

- `BLOCKED`: 8
- `MISSING`: 1
- `PASS`: 12

## Requirements

- `0_prd` / PRD exists: `PASS`
  - evidence: `docs/experiments/EXP_physeditworld_50h_prompt_gravity_lingbotfast.md`
  - detail: file exists
- `0_prd` / status doc exists: `PASS`
  - evidence: `docs/physeditworld_50h_current_status.md`
  - detail: file exists
- `0_migration` / environment export: `PASS`
  - evidence: `reports/migration/environment_no_builds.yml`
  - detail: file exists
- `0_migration` / pip freeze export: `PASS`
  - evidence: `reports/migration/pip_freeze.txt`
  - detail: file exists
- `0_migration` / required weights manifest: `PASS`
  - evidence: `reports/migration/required_weights_manifest.tsv`
  - detail: file exists
- `0_migration` / required data manifest: `PASS`
  - evidence: `reports/migration/required_data_manifest.tsv`
  - detail: file exists
- `0_migration` / rsync dry-run script: `PASS`
  - evidence: `scripts/migration/rsync_h20_to_pai_dryrun.sh`
  - detail: file exists
- `0_migration` / guarded rsync execute script: `PASS`
  - evidence: `scripts/migration/rsync_h20_to_pai_execute.sh`
  - detail: file exists
- `0_migration` / PAI/NAS and data readiness: `BLOCKED`
  - evidence: `reports/migration/physeditworld_pai_readiness.json`
  - detail: decision=PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED
  - next: mount NAS and selected PhysEditWorld 50h root
- `0_migration` / migration asset validation: `BLOCKED`
  - evidence: `reports/migration/migration_asset_validation.json`
  - detail: decision=MIGRATION_ASSET_VALIDATION_NAS_BLOCKED
  - next: mount NAS and rerun migration asset validation before execute copy
- `0_migration` / explicit copy-plan template: `PASS`
  - evidence: `reports/migration/approved_copy_manifest_template.tsv`
  - detail: file exists
- `1_data_audit` / strict selected 50h manifest: `BLOCKED`
  - evidence: `manifests/physeditworld_50h_all.jsonl`
  - detail: rows=0, required>=1
  - next: mount selected PhysEditWorld 50h root and rerun manifest audit
- `1_data_audit` / train split manifest: `BLOCKED`
  - evidence: `manifests/physeditworld_50h_train.jsonl`
  - detail: rows=0, required>=1
  - next: rerun replay-group split
- `1_data_audit` / split summary: `PASS`
  - evidence: `reports/physeditworld_50h/split_summary.md`
  - detail: file exists
- `2_conversion` / LingBot train conversion manifest: `BLOCKED`
  - evidence: `manifests/physeditworld_50h_lingbot_train.jsonl`
  - detail: rows=0, required>=1
  - next: rerun prompt-only LingBot conversion
- `2_conversion` / LingBot val conversion manifest: `MISSING`
  - evidence: `manifests/physeditworld_50h_lingbot_val.jsonl`
  - detail: manifest missing
  - next: rerun prompt-only LingBot conversion
- `3_baseline` / baseline rollout summary: `PASS`
  - evidence: `reports/physeditworld_50h_baseline_rollout/summary.md`
  - detail: file exists
- `5_checkpoint_eval` / checkpoint video/metric gate: `BLOCKED`
  - evidence: `reports/physeditworld_50h_warmup_rank32/best_checkpoint_decision.json`
  - detail: decision=CHECKPOINT_EVAL_BLOCKED_EVAL_MANIFEST_MISSING
  - next: produce true rollout videos, metrics, and Codex audit
- `7_tiny_dpo` / tiny anchored DPO gate: `BLOCKED`
  - evidence: `reports/physeditworld_tiny_dpo_v0/best_checkpoint_decision.json`
  - detail: decision=TINY_DPO_BLOCKED_INSUFFICIENT_PAIRS
  - next: build >=100 reviewed pairs before tiny DPO
- `8_ablation` / future mixed-data ablation plan: `PASS`
  - evidence: `docs/experiments/EXP_physeditworld50_plus_ourphysics50_ablation_plan.md`
  - detail: file exists
- `6_pairs` / anchored DPO pair manifest: `BLOCKED`
  - evidence: `manifests/physeditworld_dpo_pairs_anchored_v0.jsonl`
  - detail: rows=0, required>=100
  - next: run pair builder after warm-up checkpoint gate passes
