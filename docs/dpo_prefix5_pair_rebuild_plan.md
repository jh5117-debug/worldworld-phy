# DPO Prefix-5 Pair Rebuild Plan

Current audit found that `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/overnight_quant_lora_dpo_20260624_overnight_test/anchored_pairs/anchored_dpo_probe_pairs.jsonl` is not prefix_len=5. The current pairs are effectively I2V-1 because they contain `condition.image` but no `condition.prefix_len` and no `condition.prefix_video_path`.

## Goal

Build `manifests/anchored_dpo_probe_pairs_prefix5.jsonl` where each pair uses a clean five-frame prefix and compares only future frames.

## Rebuild Steps

1. For each condition, read the full 81-frame target video.
2. Extract frames 0-4 as the clean prefix condition.
3. Store a lightweight prefix clip, e.g. `prefix_len5.mp4`, or frame paths for frames 0,1,2,3,4.
4. Set manifest fields:
   - `condition.prefix_len = 5`
   - `condition.prediction_start_frame = 5`
   - `condition.prefix_video_path = <prefix clip>`
   - `condition.full_target_video_path = <clean full GT>`
   - `condition.poses` and `condition.intrinsics` remain full 81-frame aligned.
5. Keep frames 0-4 clean for both winner and loser.
6. Build winner future from frames 5-80 of clean GT or a quality-approved rollout.
7. Build corrupted negatives by modifying only frames 5-80. Do not corrupt frames 0-4.
8. Set `winner.future_video` and `loser.future_video`, or record `future_frame_indices = [5..80]`.
9. DPO loss must mask out frames 0-4 and compute energy only on frames 5-80.
10. Reward scoring must also mask out frames 0-4 and score only future frames.
11. Re-run pair visual audit and require `effective_prefix_mode = V2V-5` before any DPO preflight.

## Quality Gate

A rebuilt pair is eligible only if:

- prefix clip exists and decodes;
- winner/loser share the same condition hash;
- winner quality is acceptable;
- loser is not black/collapsed/frozen;
- loser is a hard negative in camera/background/foreground/physics/reobserve, not a pure collapse;
- `use_action=false` is preserved.
