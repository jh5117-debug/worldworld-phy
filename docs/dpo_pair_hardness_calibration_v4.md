
# DPO Pair Hardness Calibration v4

Current Status: PASS_MEDIUM_HARD_GATE_WITH_TYPEM_NOTE

Updated: 2026-06-30 12:09:54

## Hardness Classes

- `TOO_SUBTLE`: reward margin too small, visual difference unclear, or subreward/failure mismatch.
- `TOO_DEGRADED`: blur, collapse, low visual quality, too-large reward gap, or winner/loser quality failure.
- `MEDIUM_HARD`: clear and readable loser with positive reward margin, aligned subreward drop, and sharpness/quality pass.

## Initial Gate

Saved config: `reports/dpo_pair_hardness_v4/hardness_gate_config.json`.

Key thresholds:

- visual_quality >= 1
- loser_sharpness_ratio >= 0.65
- reward_margin in [0.12, 0.40]
- subreward alignment margin >= 0.05
- blur cannot be the main failure except diagnostic-only TypeB

## v4 Outcome

- TypeA sweep rows: 136
- TypeA+ accepted: 34
- TypeM accepted: 8
- TypeB usable: 0
- TypeB diagnostic blur failed: 16

TypeM accepted count is below the desired 10-30 range, so Protocol v4 is suitable for a small DPO smoke but should continue adding clearer TypeM variants before larger use.
