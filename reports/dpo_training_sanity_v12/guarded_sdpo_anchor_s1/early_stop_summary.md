Current Status: DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL

# Guarded SDPO Anchor S1 Early Stop

- Objective: `strict_sdpo` / Guarded-SDPO-Anchor proxy.
- Scope: `L0_camera_r4`.
- Train subset: `manifests/dpo_v12_subsets/s1_tiny_dpo_32.jsonl`.
- Cache status: `32/32 PASS`.
- Requested steps: 20.
- Completed rows before manual stop: `11`.
- Mean winner_improvement_post: `-7.748603820800781e-07`.
- Final winner_improvement_post: `-0.00018405914306640625`.
- Mean loser_degradation_post: `-2.373348582874645e-06`.
- Final loser_degradation_post: `1.1920928955078125e-05`.
- Mean winner_contribution_ratio_post: `0.43831473876668603`.
- Final winner_contribution_ratio_post: `0.0`.
- Mean DPO loss: `0.6931492632085626`.
- Final DPO loss: `0.6931530833244324`.
- Checkpoints saved locally: step0 / step5 / step10.
- Checkpoint video eval: `NOT_RUN_EARLY_STOP_SIGNAL_FAIL`; no PASS is claimed.

## Why Stopped

- By step10 the mean winner improvement had turned slightly negative.
- Steps 8-10 had `winner_contribution_ratio_post = 0.0`.
- DPO loss stayed near 0.693, indicating no meaningful preference signal.
- The run met the user stop policy for winner-worse / no-signal behavior.

## Decision

`DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`. Do not continue this objective or scale DPO until the objective is revised.
