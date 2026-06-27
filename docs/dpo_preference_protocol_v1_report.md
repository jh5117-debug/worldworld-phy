# DPO Preference Protocol v1 Report

Updated: 2026-06-28T00:20:04

## Scope

This round only builds preference pairs. It does not train DPO, StageB, GRPO, or full-data StageA.

## Inputs

- Prefix5 base pairs: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Screen rollout conditions: `manifests/screen16_v2v5.jsonl`
- Existing rollout pool: Original Fast, StageA V2V-5 final, DPO step20 outputs.

## Outputs

- Pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`
- Local corruption audit: `reports/dpo_preference_protocol_v1/local_corruption_audit.csv`
- Rollout scores: `reports/dpo_preference_protocol_v1/rollout_scores.csv`
- Rollout video audit: `reports/dpo_preference_protocol_v1/rollout_video_audit.csv`
- Selected medium-hard losers: `reports/dpo_preference_protocol_v1/selected_medium_hard_losers.csv`
- Pair audit: `reports/dpo_preference_protocol_v1/pair_audit.csv`
- Pair energy audit: `reports/dpo_preference_protocol_v1/pair_energy_audit.csv`
- Report root: `reports/dpo_preference_protocol_v1`

## Counts

| Category | Count |
|---|---:|
| rollout pool | 48 |
| quality-floor pass rollout | 48 |
| selected medium-hard rollout losers | 16 |
| Type A local corruption pairs | 50 |
| Type B GT vs rollout pairs | 16 |
| Type C pairs | 0 |
| total pairs | 66 |
| valid pairs | 66 |

## Pair Protocol

Every pair uses:

- `condition.prefix_len = 5`
- `condition.prediction_start_frame = 5`
- prefix frames 0-4 as condition
- winner/loser future frames 5-80
- `loss_frame_indices = 5..80`
- `reward_frame_indices = 5..80`
- `same_prefix/same_prompt/same_poses/same_intrinsics = true`

## Quality Decision

Protocol v1 has enough valid pairs for a small DPO attempt, but the recommended first subset is Type A local corruption only. Type B rollout losers are useful but should be used cautiously because the rollout pool still has hallucinated objects and weak physical events.

## Energy Audit

- real backend available: True
- real sampled energy count: 5
- proxy energy count: 61
- status: `PARTIAL_REAL_SAMPLE_PLUS_PROXY_TRIAGE`

Full all-pair real LingBot-Fast energy audit was not launched in this round because it would be expensive and this task explicitly excludes DPO training. It must be run on the selected subset immediately before training.

## Final Decision

`PROTOCOL_READY_FOR_REVIEW_NOT_TRAINING_AUTOMATION`.

The pair generation protocol is stable enough to review and to feed a future small DPO run after full real-energy audit. Do not start DPO automatically from this report.
