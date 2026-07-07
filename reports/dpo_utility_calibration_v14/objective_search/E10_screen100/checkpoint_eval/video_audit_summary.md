# E10 Step0 vs Step100 Visual Audit

Decision: `VISUAL_GATE_FAIL_STEP100_WORSE`

E10 (`calibrated_winner_detached_log`, L2 camera-temporal r4) passed the 100-step training-signal gate, but failed the true V2V-5 checkpoint video gate.

Training signal:
- Rows: 100/100
- Final winner improvement: +0.0004041791
- Mean winner improvement: +0.0001850957
- Mean winner contribution ratio: 0.824683
- Mean loser degradation: -0.0001279259

Video audit:
- Reviewed 4/4 fixed val samples from true V2V-5 rollouts.
- Step100 is worse than step0 on 2/4 samples and not decisively better on the remaining samples.
- Main regressions: duplicate green balls/foreground fragments, object identity clutter, and persistent artifact/crowding in late frames.

Conclusion:
- E10 has healthy training gap metrics but is not a valid DPO recipe.
- Do not scale, do not train400, and do not run large DPO from E10.
