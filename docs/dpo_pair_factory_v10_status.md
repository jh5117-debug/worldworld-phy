Current Status:
PAIR_FACTORY_V10_READY_50_SYNTHETIC_MIXED

# DPO Pair Factory v10 Status

## Priority
The current priority is DPO preference pair data, not objective debugging or DPO training. v10 focuses on condition recovery, existing pair re-audit, medium-hard loser mining, metrics, reward scoring, and PPT-ready visualization.

## Completed Milestones
- PRD created and pushed in `e3f9e2a`.
- Prefix5 condition inventory/recovery completed and pushed in `8da89c2`.
- Runnable prefix5 conditions recovered: 102.
- Existing pair strict re-audit completed and pushed in `254a80f`.
- Existing strict DPO-ready pairs: 18 total, including 15 GT>C and 3 TypeA_plus.
- C-rollout smoke on v10 condition pool was attempted, but policy runtime init did not reach shard/GPU generation in the bounded window. No expanded rollout was launched.
- Synthetic visible TypeM-v10 negatives generated: 63 ready pairs from 80 attempted conditions.
- Combined ready manifest count: 81 pairs.

## Current Ready Pair Composition
- Existing GT>C reviewed rollout-derived pairs: 15.
- Existing TypeA_plus human-visible pairs: 3.
- New TypeM-v10 controlled synthetic visible pairs: 63.
- Combined: 81 DPO-ready data-pool pairs.

## Condition Pool
- Runnable prefix5 conditions recovered: 102.
- Template coverage: collision 36, containment 27, drop 17, roll 22.
- Camera coverage: orbit_left_44 27, orbit_left_72 17, orbit_right_60 22, orbit_right_64 30, strafe_left_180 6.

## Existing Pair Audit Result
Strict ready pairs are limited to v6b reviewed GT>C pairs and v5 human-visible pairs. Old v1/v2/v3 broad TypeA pairs are not counted as DPO-ready because later visual alignment showed many reward-selected/local-corruption pairs are too subtle for human-visible medium-hard preference learning.

## Synthetic Pair Decision
The v10 synthetic visible negatives pass the 50-pair data gate when combined with existing strict pairs. They must be labeled as controlled synthetic TypeM-v10 negatives, not true rollout TypeB losers. They are appropriate for DPO pair visualization/metrics and a tiny data smoke, but true rollout loser expansion still needs a stable persistent V2V-5 runtime.

## Not Run
- No DPO / SDPO / Linear-DPO / Safe-linear training.
- No large DPO.
- No StageA / StageB / GRPO / broad-LoRA.
- No checkpoint or weight modification.
- No media files pushed.
