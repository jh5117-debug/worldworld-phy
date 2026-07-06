# Large Cleanup Candidates Requiring Explicit Approval

Generated: 2026-07-06T10:34:48.348722

The failed full-data warmup loser-source local media was deleted separately. The entries below are large but are not safe to delete automatically because they may contain checkpoints, training/eval lineage, generated data, or pair-factory assets referenced by manifests/docs.

| Path | Size | Policy | Reason |
|---|---:|---|---|
| `local_assets/dpo_training_sanity_v12` | 18G | needs_user_approval_checkpoint_or_eval_state | old_v12_training_cache_and_rollouts |
| `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505` | 18G | needs_user_approval_experiment_artifact | old_stageA_data_gate_experiment |
| `local_assets/dpo_training_sanity_v12/guarded_sdpo_anchor_s1` | 8.6G | needs_user_approval_dpo_debug_artifact | failed_v12_guarded_sdpo_cache_rollouts |
| `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49_retry4` | 4.3G | needs_user_approval_cache | old_scope_sanity_cache_retry4 |
| `local_assets/overnight_quant_lora_dpo_20260624_overnight_test` | 3.3G | needs_user_approval_experiment_artifact | old_overnight_quant_lora_dpo_outputs |
| `local_assets/dpo_objective_repair_v12b` | 3.3G | keep_for_current_lineage_unless_confirmed | v12b_winner_anchor_repair_artifacts |
| `local_assets/dpo_pair_cache_v8m` | 3.0G | needs_user_approval_cache | old_pair_cache_v8m |
| `local_assets/dpo_objective_cache_v8j` | 1.4G | needs_user_approval_cache | old_objective_cache_v8j |
| `local_assets/dpo_pair_factory_v11/synthetic_pairs` | 1.9G | keep_dataset_asset | ready500_synthetic_pair_media |
| `local_assets/dpo_pair_factory_v11/synthetic_pairs_extra` | 776M | keep_dataset_asset_or_confirm | ready500_extra_synthetic_pair_media |
| `local_assets/dpo_pair_factory_v10` | 1.2G | needs_user_approval_dataset_lineage | v10_pair_factory_assets |
| `local_assets/experiments/small_lora_scope_sweep_20260624` | 1.1G | keep_old_C_reference_unless_confirmed | old_small_lora_sweep_adapters_rollouts |

## Deletion Rule

Do not delete these directories unless the user provides an explicit whitelist or confirms that the named lineage is no longer needed. This avoids deleting old C references, ready500 assets, checkpoints, or recoverable pair-factory data by accident.


## Partial Cleanup Executed - 2026-07-06 10:43 CST

The Jun-22 StageA data-gate directory was not deleted wholesale, but its old optimizer `training_state.pt` files were removed. The failed v12 strict-SDPO cache directory was also removed. Remaining large candidates still require explicit confirmation.


## Additional Cleanup Executed - 2026-07-06 10:45 CST

Removed old non-current Jun-22 StageA gate checkpoint directories and old overnight rollout media. Remaining large directories are current data assets or explicit reference assets unless separately approved.
