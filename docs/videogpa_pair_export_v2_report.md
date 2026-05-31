# VideoGPA Pair Export V2 Report

## Pair Builds

- Fresh `gt_vs_corrupt` with requested `min_margin=0.15`: `0` kept pairs, `10` rejected over 2 samples.
- Fresh `gt_vs_fast_rollout` from reward v5: `2` kept pairs, `0` rejected.
- Existing prior `gt_vs_corrupt` smoke fallback: first 2 rows were inspected, but their older schema lacks complete camera condition paths, so they are not the main encode-smoke source.

## Exported Files

- `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/gt_vs_fast_pairs.jsonl`
- `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/videogpa_gt_vs_fast_pairs.json`
- `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/videogpa_gt_vs_corrupt_pairs.json`
- `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/videogpa_gt_vs_corrupt_pairs_fallback_existing.json`

## Valid Fresh Pairs

- Pair count: `2`
- Pair type: `clean Physion GT > LingBot-Fast rollout`
- Winner videos: existing `target.mp4` files under `local_assets/data/physion/processed/lingbot_cam_inputs/smoke/`
- Loser videos: existing `generated.mp4` files under `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/`
- Reward source: `local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v5/scores.jsonl`
- Reward margin: confidence-weighted reward v5.

## Metadata Preservation

- Prompt preserved: yes.
- Input image preserved: yes.
- `poses.npy` preserved in `extra_condition`: yes.
- `intrinsics.npy` preserved in `extra_condition`: yes.
- `metadata.json` preserved in `extra_condition`: yes.
- `use_action=false` preserved: yes.
- Dummy action remains compatibility-only and is not a core condition.
- Reward v5 breakdown is retained in pair metadata.

## VideoGPA Native Fields

VideoGPA understands the group/video metadata and scores. It does not natively know `extra_condition.camera_condition`, poses, intrinsics, or LingBot dummy-action semantics. These are sidecar inputs for a future LingBot-Fast wrapper.
