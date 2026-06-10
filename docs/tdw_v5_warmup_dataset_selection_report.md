# TDW v5 Warmup Dataset Selection Report

Date: 2026-06-10

Selected dataset:

`TDW v5 aggressive 2x 200 human_approved_all`

Reason:

- Human review accepted the motion scale.
- Conversion and file integrity gates passed 200/200.
- Train/val/test split exists and was already used by dataloader and Stage A warmup gates.
- No new TDW generation is safe in this turn without TDW display approval.

Known split:

- train: 160
- val: 20
- test: 20

Known full dataset template distribution:

- drop: 60
- collision: 60
- roll: 40
- containment: 40

Known Stage A balanced sampler coverage:

- 60 train steps;
- drop/collision/roll/containment = 15/15/15/15.

Decision:

Use v5 200 for rollout/reward pipeline gates. Do not scale to 1k in this turn.
