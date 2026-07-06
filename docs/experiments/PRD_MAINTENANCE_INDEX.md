# PRD Maintenance Index

Updated: 2026-07-06 10:47 CST

## Current Active Decision

The current objective was to evaluate `fulldata-lingbotfast-warmup-weights` as a DPO-loser source and, only if Codex visual review approved, scale to 500 generated loser videos on H20 GPU4-7.

Decision: `FULLDATA_WARMUP_CHECKPOINT_SELECT_NO_GO_FOR_500`.

Evidence:

- Final adapter smoke generated 2/2 videos but was not better than old C.
- Intermediate checkpoints `step_000103`, `step_000206`, `step_000309`, and `step_000412` generated reviewed `01002` contact sheets but were not visually better than old C.
- Common failure: missing red/green physical response, green sphere mostly static, red sphere drifts to boundary, late duplicate/color fragments.
- The multi-condition checkpoint-selection smoke stalled before completing `01008`.
- 500-video generation was not launched.

Primary files:

- `docs/experiments/EXP_fulldata_lingbotfast_warmup_loser_eval.md`
- `docs/fulldata_lingbotfast_warmup_loser_eval_status.md`
- `docs/fulldata_lingbotfast_warmup_loser_eval_report.md`
- `reports/dpo_pair_factory_v11/new_c_warmup_loser_checkpoint_select/checkpoint_selection_visual_audit.md`

## Active Data / Weight Assets To Keep

| Asset | Reason |
|---|---|
| `local_assets/stageA_v2v5_all_available_c_r4_2epoch_retry1` | Current `fulldata-lingbotfast-warmup-weights` lineage. |
| `local_assets/experiments/small_lora_scope_sweep_20260624` | Old C reference / loser-source baseline used by pair manifests. |
| `local_assets/dpo_pair_factory_v11/synthetic_pairs` | ready500 pair-factory asset. |
| `local_assets/dpo_pair_factory_v11/synthetic_pairs_extra` | extra v11 synthetic controlled pair media; keep unless user confirms. |
| `local_assets/data/physion` | raw/local condition data. |
| `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl` | canonical repaired ready500 manifest. |

## Cleanup Completed

Repo-local `local_assets` was reduced from about 58G to about 16G. `/home/nvme04` available space increased from about 303G to about 345G.

Deleted categories:

- Failed full-data warmup loser smoke local media.
- Old regenerated v8/v12 cache tensor directories.
- Old StageA data-gate optimizer `training_state.pt` files.
- Failed v12 strict-SDPO latent cache.
- Old non-current Jun-22 StageA gate checkpoint directories.
- Old overnight rollout/media package.

Cleanup evidence:

- `reports/cleanup_fulldata_warmup_loser_eval/safe_deleted_transient_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/cache_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/large_cleanup_candidates_requires_approval.md`

## Active PRDs

| PRD | Status | Notes |
|---|---|---|
| `EXP_fulldata_lingbotfast_warmup_loser_eval.md` | active final record | Current objective result and no-go decision. |
| `EXP_stageA_v2v5_all_available_c_warmup.md` | active lineage | Describes the full-data warmup that produced the evaluated weights. |
| `EXP_dpo_pair_factory_v11_scale500.md` | active data lineage | ready500 pair factory remains the current pair data asset. |
| `EXP_dpo_pair_factory_v11_repaired_manifest_and_metrics.md` | active data freeze | canonical repaired ready500 and metric backend status. |
| `EXP_v11_ready500_loser_quality_and_metrics_backend.md` | active QA lineage | ready500 loser-quality / backend audit. |

## Superseded / Historical PRDs Kept For Audit Trail

| PRD group | Status | Current replacement / reason |
|---|---|---|
| `EXP_winner_preserving_objective_diagnosis_v8*.md`, `EXP_*cache*_v8*.md`, `EXP_wan_from_pretrained_split_v8g.md` | superseded | Runtime/cache diagnosis fed into the safe Wan loader patch; no longer the current task. |
| `EXP_dpo_training_sanity_v12.md`, `EXP_dpo_objective_repair_v12b.md`, `EXP_tiny_guarded_preference_v12c.md`, `EXP_dpo_gpu_scheduler_v12d.md` | superseded for this objective | DPO training/objective work is not the current priority; current task is loser-source evaluation and cleanup. |
| `EXP_dpo_pair_factory_v10*.md` | superseded by v11 | v10/v10b pair data were superseded by v11 ready500 canonical data. |
| `EXP_stageA_v2v5_warmup_4900x2.md` | superseded | The actual all-available 3299-row warmup lineage is `EXP_stageA_v2v5_all_available_c_warmup.md`. |
| Early protocol PRDs `EXP_dpo_preference_protocol_v1/2/3.md`, `EXP_001/002/003/004*.md` | historical | Kept for provenance of old C, reward calibration, and pair-factory evolution. |

## PRD Deletion Policy

Do not delete historical PRD markdown files solely to save space; they are small and preserve experiment provenance. Delete or archive only generated large artifacts, caches, raw rollout media, and non-current weight directories after verifying they are not active assets.

If the user wants physical deletion of historical PRDs anyway, use this index to choose an explicit whitelist first.

## Follow-up Audit - 2026-07-06 10:56 CST

- Stopped the known stale `dpo_gpu_scheduler_v12d` tmux session after it had already failed the v12c training-signal gate. This prevents old DPO queue activity from restarting under the current loser-source cleanup objective.
- Current GPU4-7 occupants are unknown/other `python` processes, not the fulldata warmup loser-source eval task. No unknown process was killed.
- Current repo-local storage: `local_assets` about 16G, `reports` about 944M, `/home/nvme04` about 345G free.
- Added current remaining-asset audit: `reports/cleanup_fulldata_warmup_loser_eval/remaining_assets_current_audit.md`.
- No additional uncertain data/weights were deleted in this follow-up pass. Remaining non-keep GB-scale artifacts require explicit delete confirmation because they preserve DPO/v10/old rollout lineage.

