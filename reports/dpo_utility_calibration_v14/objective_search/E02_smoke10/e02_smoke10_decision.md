# E02 Smoke10 Decision

Decision: `TRAINING_SIGNAL_FAIL_WINNER` / `CALIBRATED_WINNER_DETACHED_LOG_SIGNAL_FAIL`

## Result

- Rows: 10 / 10
- Mean winner_improvement_post: 8.374452590942383e-05
- Final winner_improvement_post: -4.172325134277344e-05
- Mean winner_contribution_ratio_post: 0.6669103726560174
- Mean loser_degradation_post: -3.3074617385864256e-05
- Best step by winner improvement: 6 with winner_improvement_post=0.00028395652770996094 and dpo_loss=0.5086157321929932
- Winner-worse rows: 2
- Loser-dominant rows: 1

## Interpretation

Calibrated beta fixed the pure no-signal symptom: DPO loss moved away from 0.693. However the final step flipped winner improvement negative and final WCR dropped to 0. This is not a valid DPO recipe and must not be scaled.

## Next Objective Fix

Try E03/E02-lower-lr or E02-best-step with early stopping before final-step winner flip. Keep loser detached and preserve the winner anchor. Do not run video/metrics gate for E02_smoke10 because training signal failed.
