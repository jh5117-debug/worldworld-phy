Current Status:
PAIR_FACTORY_V10B_PRD_READY

# DPO Pair Factory v10b Status

## Starting Point
- v10 ready pairs: 81.
- Existing strict ready pairs: 18.
  - GT>C rollout-derived: 15.
  - TypeA_plus human-visible: 3.
- Synthetic visible TypeM-v10 pairs: 63.
- Final v10 manifest: `manifests/dpo_pair_factory_v10_ready_pairs.jsonl`.
- Synthetic manifest: `manifests/dpo_pair_factory_v10_synthetic_visible_pairs.jsonl`.
- Existing strict manifest: `manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl`.
- PPT showcase exists: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_ready_showcase.mp4`.

## Largest Caveat
The 63 new TypeM-v10 pairs are controlled synthetic visible negatives, not real model rollout TypeB losers. They must remain labeled separately from rollout-derived pairs.

## This Round
v10b only performs final audit, data freeze, subset construction, pair cards, data card, and documentation. It does not train or run rollout/inference.

## Not Run
- No DPO / SDPO / Linear-DPO.
- No winner-anchor.
- No StageA / StageB / GRPO / broad-LoRA.
- No checkpoint, data, or weight deletion.
- No media or local_assets push.
