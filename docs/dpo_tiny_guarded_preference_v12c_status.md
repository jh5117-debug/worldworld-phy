Current Status: V12C_WINNER_DETACHED_SIGNAL_FAIL

# DPO Tiny Guarded Preference v12c Status

Updated: 2026-07-05 11:21:55

- v12c `winner_detached_preference` ran through v12d scheduler on physical GPU4.
- Steps completed: `10` / `10`.
- Runtime exit code: `0`.
- Mean winner_improvement_post: `0.00011658668518066406`.
- Final winner_improvement_post: `-8.320808410644531e-05`.
- Mean loser_degradation_post: `-5.3834915161132815e-05`.
- Mean winner_contribution_ratio_post: `0.8491498668883544`.
- Decision: `WINNER_DETACHED_PREFERENCE_SIGNAL_FAIL` / scheduler gate `TRAINING_SIGNAL_FAIL`.

The run is not a PASS because final winner improvement is negative. No tiny loser-gradient follow-up, no S16/S32/S64, and no train400 pilot are allowed from this result.

No checkpoint video/metric/visual PASS is claimed.
