# DPO Pair Visual Audit Summary

Pair file: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/overnight_quant_lora_dpo_20260624_overnight_test/anchored_pairs/anchored_dpo_probe_pairs.jsonl`

## Counts

- total_pairs: 50
- contact_sheets_generated: 50
- codex_pair_reviews_written: 50
- valid_preference_for_prefix5_dpo: 0
- visual_preference_valid_ignoring_prefix: 50
- winner_bad_count: 0
- loser_collapsed_count: 0
- too_easy_count: 0
- missing_prefix_count: 50
- missing_winner_video_count: 0
- missing_loser_video_count: 0
- same_condition_hash_mismatch_count: 0

## Prefix Verification

Raw prefix_len distribution:
- UNKNOWN: 50

Effective prefix mode distribution:
- I2V-1: 50

Conclusion: current pairs are **not V2V-5 pairs**. They are effectively I2V-1 / first-image conditioned pairs because `condition.prefix_len` and `condition.prefix_video_path` are missing.

## Pair Type Distribution

- gt_vs_quality_bounded_rollout: 50

## Winner Source Distribution

- clean_gt: 50

## Loser Source Distribution

- A_step050: 5
- A_step100: 5
- B_step050: 5
- B_step100: 5
- C_step050: 5
- C_step100: 5
- C_step200: 4
- D_step050: 4
- D_step100: 4
- D_step200: 4
- original_fast: 4

## Corruption Type Distribution

- NONE: 50

## Required Questions

1. 当前 DPO pair 是否真的可视化审查过？  
   Yes. The script decoded every winner/loser video, sampled frames, generated one contact sheet per pair, and wrote one structured audit row per pair.

2. 总共审查了多少 pair？  
   50 pairs.

3. 有多少 pair 是 valid preference？  
   0 for prefix5 DPO. 50 are visually plausible preferences if ignoring the missing prefix5 requirement.

4. 有多少 pair 的 winner 本身质量不好？  
   0.

5. 有多少 pair 的 loser 过度崩坏、太简单？  
   loser_collapsed=0, too_easy=0.

6. 当前 pair 是否使用 prefix_len=5？  
   No.

7. 如果不是，当前到底是 I2V-1、prefix schema missing，还是 prefix path missing？  
   prefix schema is missing: no `condition.prefix_len`, no `condition.prefix_video_path`. Because `condition.image` exists, the effective mode is I2V-1.

8. 当前是否可以进入真实 DPO？  
   No. These pairs can be used for I2V diagnostics, but they should not be used as the requested prefix-aware V2V-5 DPO pairs.

9. 如果不可以，下一步要如何重建 pair？  
   Rebuild `manifests/anchored_dpo_probe_pairs_prefix5.jsonl` with frames 0-4 as clean prefix, frames 5-80 as winner/loser future, and compute DPO/reward only on the future segment.

## Output Paths

- schema audit: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_pair_visual_audit/pair_schema_audit.csv`
- pair audit CSV: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_pair_visual_audit/pair_audit.csv`
- pair audit JSONL: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_pair_visual_audit/pair_audit.jsonl`
- contact sheets: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_pair_visual_audit/pair_contact_sheets`
- contact sheet index: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_pair_visual_audit/pair_contact_sheet_index.jpg`

## Git Note

The detailed CSV/JSONL and JPG contact sheets are intentionally kept under `reports/dpo_pair_visual_audit/` and are not pushed to Git. This docs copy records the lightweight audit conclusion for repository history.
