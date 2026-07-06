# Remaining Assets Current Audit

Generated: 2026-07-06 11:02 CST

This audit reflects the repo after the fulldata warmup loser-source visual gate and cleanup passes. No uncertain data/weights were deleted in this follow-up audit.

| Path | Size | Policy | Reason | Status |
|---|---:|---|---|---|
| `local_assets/stageA_v2v5_all_available_c_r4_2epoch_retry1` | 39.3M | keep | current fulldata-lingbotfast-warmup-weights lineage | exists |
| `local_assets/experiments/small_lora_scope_sweep_20260624` | 965.3M | keep | old C reference baseline and adapters used for comparison | exists |
| `local_assets/dpo_pair_factory_v11/synthetic_pairs` | 1.81G | keep | ready500 synthetic controlled pair media | exists |
| `local_assets/dpo_pair_factory_v11/synthetic_pairs_extra` | 774.8M | keep_or_confirm | extra v11 synthetic media; user confirmation needed before deletion | exists |
| `local_assets/data/physion` | 2.75G | keep | raw/local condition data | exists |
| `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl` | 2.4M | keep | canonical repaired ready500 manifest | exists |
| `local_assets/dpo_objective_repair_v12b` | 3.28G | confirm_before_delete | DPO winner-anchor repair lineage; not current loser-source objective but useful if DPO resumes | exists |
| `local_assets/dpo_pair_factory_v10` | 1.10G | confirm_before_delete | superseded v10 pair factory media; delete only if v11 is the sole kept data lineage | exists |
| `local_assets/stageA_v2v5_20260627` | 963.4M | confirm_before_delete | old stageA v2v5 artifacts; may contain reproducibility/eval lineage | exists |
| `local_assets/targeted_BC_loser_mining_v6b` | 852.6M | confirm_before_delete | old B/C rollout mining media; docs/manifests depend on summaries | exists |
| `local_assets/overnight_quant_lora_dpo_20260624_overnight_test` | 506.4M | do_not_delete_running_reference | old overnight package still has live reward_calibration/supervisor refs | exists |
| `local_assets/dpo_objective_ablation_20260628_184115` | 402.0M | confirm_before_delete | old objective ablation artifacts | exists |
| `local_assets/dpo_prefix5_pairs_20260627_031729` | 369.4M | confirm_before_delete | old prefix5 pair media | exists |
| `local_assets/meeting_eval_20260624_011137` | 349.9M | confirm_before_delete | old meeting eval media | exists |
| `local_assets/dpo_preference_protocol_v1` | 320.8M | confirm_before_delete | early pair protocol media | exists |
| `local_assets/dpo_pair_hardness_v4` | 284.8M | confirm_before_delete | old hardness/pair media | exists |
| `local_assets/dpo_training_sanity_v12` | 170.1M | confirm_before_delete | old DPO sanity artifacts now small after cache cleanup | exists |
| `local_assets/dpo_tiny_guarded_preference_v12c` | 75.4M | confirm_before_delete | old tiny guarded DPO artifacts; scheduler stopped | exists |

## Follow-up action

- Stopped known stale `dpo_gpu_scheduler_v12d` tmux session because the current objective is not DPO training and its first training gate had already failed.
- Did not kill unknown GPU processes.
- Did not delete current warmup weights, old C reference, ready500 media, or raw condition data.
- Remaining GB-scale non-keep artifacts are marked `confirm_before_delete`; deleting them would be a policy choice rather than an automatically safe cleanup.
