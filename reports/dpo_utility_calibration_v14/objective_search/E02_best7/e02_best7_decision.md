# E02 Best7 Decision

Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY_V14` / `TRAINING_SIGNAL_PASS`

## Result

- Scheme: `E02_best7`
- Objective: `calibrated_winner_detached_log`
- Scope: `L0_camera_r4`
- Utility: `u_log`
- Beta: `1000.0`
- Rows: `7` / `7`
- Mean winner_improvement_post: `0.00010894877570016044`
- Final winner_improvement_post: `0.00033855438232421875`
- Mean winner_contribution_ratio_post: `0.6667287038434788`
- Mean loser_degradation_post: `-2.8984887259347098e-05`
- Final health flags: `WINNER_IMPROVES;LOSER_DEGRADES`
- Checkpoints saved locally: `3`

## Interpretation

E02_best7 is the first v14 run with positive mean and final winner improvement after beta calibration. It also keeps loser dominance low and moves the preference loss away from the 0.693 no-signal regime.

This is not a complete DPO recipe yet. Per v14 gate, checkpoint videos, metrics, and Codex visual audit must pass before it can be called `DPO_RECIPE_FOUND_200STEP_V14` or scaled to S16/S32.

## Next Gate

Run checkpoint eval for step0, step5, and step7 on `manifests/dpo_v12b_subsets/val_video_4.jsonl`, using only physical GPU4/5. Required outputs are real V2V-5 videos under local_assets, metrics under reports, contact sheets, and Codex visual audit.
