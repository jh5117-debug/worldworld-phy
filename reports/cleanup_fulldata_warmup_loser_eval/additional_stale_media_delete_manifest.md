# Additional Stale Media Delete Manifest

Generated: 2026-07-06 11:10 CST

This pass deletes old local media/cache outputs only. It preserves current fulldata warmup weights, old C reference, v11 ready500 media, raw condition data, and v12b DPO repair lineage.

| Path | Size | Reason | Action |
|---|---:|---|---|
| `local_assets/dpo_pair_factory_v10` | 1.10G | superseded_by_v11_ready500_canonical | planned_delete |
| `local_assets/stageA_v2v5_20260627` | 963.4M | old_stageA_v2v5_pilot_outputs_superseded_by_all_available_retry1 | planned_delete |
| `local_assets/targeted_BC_loser_mining_v6b` | 852.6M | old_BC_rollout_media_superseded_by_v11_ready500_and_reports | planned_delete |
| `local_assets/dpo_objective_ablation_20260628_184115` | 402.0M | old_objective_ablation_media_not_current_objective | planned_delete |
| `local_assets/dpo_prefix5_pairs_20260627_031729` | 369.4M | old_prefix5_pair_media_superseded_by_v11_ready500 | planned_delete |
| `local_assets/meeting_eval_20260624_011137` | 349.9M | old_meeting_eval_media | planned_delete |
| `local_assets/dpo_preference_protocol_v1` | 320.8M | early_pair_protocol_media_superseded_by_v11 | planned_delete |
| `local_assets/dpo_pair_hardness_v4` | 284.8M | old_hardness_media_superseded_by_v11_loser_audit | planned_delete |
| `local_assets/dpo_training_sanity_v12` | 170.1M | failed_or_superseded_DPO_sanity_local_media_current_objective_not_DPO | planned_delete |
| `local_assets/dpo_tiny_guarded_preference_v12c` | 75.4M | failed_tiny_DPO_local_media_scheduler_stopped | planned_delete |
| `local_assets/dpo_probe_v2v5_20260627` | 162.8M | old_probe_media | planned_delete |
| `local_assets/targeted_BC_loser_mining_v6` | 146.5M | old_v6_rollout_media_superseded_by_v6b_v11_reports | planned_delete |
| `local_assets/dpo_smoke_v7` | 144.0M | old_tiny_DPO_smoke_local_media_signal_fail | planned_delete |
| `local_assets/v2v5_rollouts_20260627_1000` | 75.2M | old_v2v5_rollout_media | planned_delete |
| `local_assets/v2v5_rollouts_20260627_082915` | 71.1M | old_v2v5_rollout_media | planned_delete |
| `local_assets/v2v5_rollouts_20260627_0938` | 30.7M | old_v2v5_rollout_media | planned_delete |
| `local_assets/v2v5_rollouts_20260627_081415` | 7.7M | old_v2v5_rollout_media | planned_delete |
| `local_assets/v2v5_rollouts_20260627_080928` | 25.4K | old_v2v5_rollout_media | planned_delete |
| `local_assets/dpo_objective_smoke_v3` | 23.2M | old_objective_smoke_media | planned_delete |
| `local_assets/stageA_v2v5_all_available_c_r4_2epoch` | 2.7M | failed_first_attempt_superseded_by_retry1 | planned_delete |
| `local_assets/eval_metrics_20260627_005649` | 1.6M | old_metric_media | planned_delete |
| `local_assets/stageA_v2v5_pilot_20260627` | 775.1K | old_stageA_pilot_media | planned_delete |
