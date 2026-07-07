# E03 Smoke10 Decision

Decision: `TRAINING_SIGNAL_FAIL_WINNER` / `EARLY_STOP_WINNER_WORSE`

E03 used lower LR and lower lambda_pref than E02, but it showed `WINNER_WORSE` by step 1. Following the gate policy, the E03 process was stopped early instead of running all 10 steps.

- Rows completed: 2
- Final winner_improvement_post: -8.20159912109375e-05
- Final WCR: 0.0
- Final dpo_loss: 0.857638955116272
- Winner-worse rows: 1

Interpretation: simply lowering LR/lambda_pref did not fix the final/winner instability. Next safer candidate is best-step early stop around E02 step 6 or stronger winner-only regularization, not scale.
