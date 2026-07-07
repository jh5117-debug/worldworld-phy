# E09 Step0 vs Step50 Visual Audit

Decision: `VISUAL_GATE_FAIL_STEP050_WORSE`

E09 (`source_weighted_rollout_priority`, L0 camera r4, calibrated winner-detached log utility) reached a strong early training signal at step50, but failed the required true V2V-5 checkpoint video gate.

Training signal at step50:
- Winner improvement post: +0.0014111996
- Winner contribution ratio: 1.0
- Loser degradation post: -0.0013124943
- DPO loss: 0.5111857

Video audit:
- Reviewed 4/4 fixed val samples from true V2V-5 rollouts.
- Step50 is worse than step0 on 3 samples and not better on the remaining sample.
- Main regressions: foreground duplication, green/blob object pollution, yellow/white line or text-like artifacts, and scene contamination.

Conclusion:
- E09 is a strong training-signal candidate but not a valid DPO recipe.
- Do not scale, do not train400, and do not run large DPO from E09.
