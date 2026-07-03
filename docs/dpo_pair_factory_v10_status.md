Current Status:
PAIR_FACTORY_V10_CONDITION_READY_EXISTING_PAIRS_INSUFFICIENT

# DPO Pair Factory v10 Status

## Priority
The current priority is DPO preference pair data, not objective debugging or DPO training. v10 focuses on condition recovery, existing pair re-audit, medium-hard loser mining, metrics, reward scoring, and PPT-ready visualization.

## Completed Milestones
- PRD created and pushed in `e3f9e2a`.
- Prefix5 condition inventory/recovery completed and pushed in `8da89c2`.
- Runnable prefix5 conditions recovered: 102.
- Template coverage: collision 36, containment 27, drop 17, roll 22.
- Camera coverage: orbit_left_44 27, orbit_left_72 17, orbit_right_60 22, orbit_right_64 30, strafe_left_180 6.
- Existing pair strict re-audit completed.
- Existing strict DPO-ready pairs: 18 total, including 15 GT>C and 3 TypeA_plus.

## Existing Pair Audit Result
Strict ready pairs are limited to v6b reviewed GT>C pairs and v5 human-visible pairs. Old v1/v2/v3 broad TypeA pairs are not counted as DPO-ready because later visual alignment showed many reward-selected/local-corruption pairs are too subtle for human-visible medium-hard preference learning.

Status counts:
- DPO_READY_EXISTING_STRICT: 18
- REVIEW_REQUIRED_OLD_SUBTLE_RISK: 134
- REVIEW_REQUIRED_UNMAPPED_AUDIT: 39
- REJECT_TECHNICAL_OR_LABEL_GATE: 4

## Decision
Existing pairs alone are insufficient for the v10 target of 50+ reviewed DPO-ready pairs. The next required step is to use the 102 runnable prefix5 condition pool for expanded B/C loser mining and/or clearly visible synthetic medium-hard negative construction, followed by metric scoring and Codex visual audit.

## Not Run
- No DPO / SDPO / Linear-DPO / Safe-linear training.
- No large DPO.
- No StageA / StageB / GRPO / broad-LoRA.
- No checkpoint or weight modification.
- No media files pushed.
