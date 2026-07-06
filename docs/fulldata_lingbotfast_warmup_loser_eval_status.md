# Full-data LingBotFast Warmup Loser Eval Status

Status: `NEW_C_SMOKE_NOT_BETTER_THAN_OLD_C_ON_2COND`

## Summary

The full-data warmup adapter can generate V2V-5 videos after patching `run_v2v5_inference.py` to use the v8g safe `WanModelFast.from_pretrained` args. The default LingBot `WanI2VFast` path stalled before GPU generation.

Smoke output:

- New rollout root: `local_assets/dpo_pair_factory_v11/new_c_warmup_loser_smoke/M_C_all_available_final_safe_2cond`
- Contact sheets: 2/2
- Future videos: 2/2
- Metrics: `reports/dpo_pair_factory_v11/new_c_warmup_loser_smoke/new_vs_old_c_metrics.csv`
- Visual audit: `reports/dpo_pair_factory_v11/new_c_warmup_loser_smoke/new_vs_old_c_visual_audit.md`

## Codex Visual Decision

Do not launch 500-video generation yet.

- Sample `01002`: new C is clear and usable, but visually almost identical to old C. Both miss the physical event.
- Sample `01008`: new C is clear, but shows disappearance/duplicate-fragment artifacts and is not better than old C.

## Runtime Fix

Added `--safe_wan_from_pretrained` and `--safe_wan_from_pretrained_log` to `cam_physgeo/eval/run_v2v5_inference.py`. This forces:

- `local_files_only=True`
- `use_safetensors=True`
- `low_cpu_mem_usage=True`

## Cleanup

No files were deleted. A cleanup inventory was written:

- `reports/cleanup_fulldata_warmup_loser_eval/cleanup_inventory.md`
- `reports/cleanup_fulldata_warmup_loser_eval/cleanup_inventory_top.csv`


## Checkpoint Selection Update - 2026-07-06 10:26 CST

Status: `FULLDATA_WARMUP_CHECKPOINT_SELECT_NO_GO_FOR_500`

Intermediate checkpoints `step_000103`, `step_000206`, `step_000309`, and `step_000412` were smoke-tested on GPU4-7 with the safe V2V-5 loader.

- Each checkpoint produced 1 reviewed `01002` future/contact sheet.
- None was visually better than old C or the final full-data checkpoint.
- Common failure: physical contact event missing, green object mostly static, red object drifts to boundary, late duplicate/color fragments.
- The runner stalled before completing the second selected condition, so the four smoke processes were terminated to free GPU4-7.
- 500-video generation was not launched.

Audit path: `reports/dpo_pair_factory_v11/new_c_warmup_loser_checkpoint_select/checkpoint_selection_visual_audit.md`.


## Cleanup Update - 2026-07-06 10:35 CST

Safe transient cleanup performed:

- Deleted `local_assets/dpo_pair_factory_v11/new_c_warmup_loser_checkpoint_select` (33M), failed checkpoint-selection local media.
- Deleted `local_assets/dpo_pair_factory_v11/new_c_warmup_loser_smoke` (21M), failed final-adapter local media.

Large cleanup candidates requiring explicit whitelist were recorded at:

- `reports/cleanup_fulldata_warmup_loser_eval/large_cleanup_candidates_requires_approval.md`
- `reports/cleanup_fulldata_warmup_loser_eval/large_cleanup_candidates_requires_approval.csv`

No checkpoints, raw data, training weights, ready500 dataset assets, or old C reference assets were deleted automatically.


## Cache-Only Cleanup Update - 2026-07-06 10:38 CST

Deleted old regenerated cache tensor directories only:

- `local_assets/dpo_pair_cache_v8m` (3.0G)
- `local_assets/dpo_objective_cache_v8j` (1.4G)
- `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49` (2.2G)
- `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49_retry2` (2.2G)
- `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49_retry4` (4.3G)
- `local_assets/dpo_objective_cache_v8i` (271M)
- `local_assets/dpo_objective_cache_v8d` (12K)

Freed approximately 13G. `/home/nvme04` available space increased to about 316G.

Deletion manifest:

- `reports/cleanup_fulldata_warmup_loser_eval/cache_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/cache_deleted_manifest.md`

No raw data, model weights, adapters/checkpoints, ready500 assets, old C reference assets, or full-data warmup weights were deleted.


## Old Experiment State Cleanup - 2026-07-06 10:43 CST

Deleted additional old experiment artifacts:

- Old Jun-22 StageA data-gate optimizer `training_state.pt` files only, leaving adapter states/manifests/log lineage in place.
- Failed v12 strict-SDPO regenerated latent cache `local_assets/dpo_training_sanity_v12/guarded_sdpo_anchor_s1/cache_s1_window49_run1`.

Freed approximately 20G more. Repo `local_assets` is now about 25G; `/home/nvme04` available space is about 336G.

Deletion evidence:

- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_deleted_manifest.md`
- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_delete_verify.txt`

Kept:

- current `fulldata-lingbotfast-warmup-weights`
- old C reference adapter assets
- ready500 / pair-factory dataset assets
- raw Physion/local condition data
- adapter_state files from the old StageA gate


## Old Weight/Rollout Cleanup Update - 2026-07-06 10:45 CST

Deleted old non-current experiment checkpoint/adapter directories and rollout media:

- Jun-22 `fast_stageA_high_only_data_gate_20260622_135505` checkpoint directories after optimizer states were already removed.
- Old `overnight_quant_lora_dpo_20260624_overnight_test` rollout/media package.

Freed approximately 9.7G more. Repo `local_assets` is now about 16G; `/home/nvme04` available space is about 345G.

Deletion evidence:

- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_deleted_manifest.md`
- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_delete_verify.txt`

Still kept:

- current `fulldata-lingbotfast-warmup-weights`
- old C reference sweep `local_assets/experiments/small_lora_scope_sweep_20260624`
- ready500 / v11 pair-factory assets
- raw Physion/local condition data
