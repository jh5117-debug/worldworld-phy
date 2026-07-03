Current Status: STARTED

# DPO Pair Factory v11 Status

Generated: 2026-07-03 23:17:13

## Starting Point

- v10b ready pairs: 81
- v10b rollout-derived GT>C: 15
- v10b controlled synthetic TypeM-v10: 63
- v10b TypeA_plus controlled: 3
- v10b top50 balanced exists.

## New Priority

The current priority is data scale, not DPO objective work. v11 targets 500 reviewed DPO-ready preference pairs. No DPO training, SDPO, Linear-DPO, winner-anchor, StageA, StageB, GRPO, or broad-LoRA is run in this experiment.

## Success Target

- Minimum: 500 reviewed DPO-ready pairs.
- Stretch: 800 candidate pairs, 500 strict ready pairs, and 100 real rollout-derived pairs if runtime allows.
- Every ready pair must have prefix/WIN/LOSE, contact sheet, reward/metrics, and Codex visual audit with written reason.
