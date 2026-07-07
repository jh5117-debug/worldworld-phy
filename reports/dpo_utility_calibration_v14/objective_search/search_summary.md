# v14 Objective Search Current Summary

Decision: `DPO_RECIPE_NOT_FOUND_V14`

The v14 calibrated search fixed the earlier no-signal problem at the training-gap level, but did not find a recipe that passes the required true-video gate.

## Training Signal

- E07, E08, E09, and E10 all produced positive winner-improvement signals with nonzero updates.
- E09 step50 was the cleanest early gap signal: winner improvement +0.001411, WCR 1.0, loser degradation negative.
- E10 completed 100/100 with mean winner improvement +0.000185 and WCR 0.8247.

## Video Gate

- E07 failed: step200 worse than step0 on 4/4 fixed val samples.
- E09 failed: step50 worse/not-better on 4/4 fixed val samples.
- E10 failed: step100 worse on 2/4 and not decisively better on the rest.
- E08 remains training-signal-only and is not a valid recipe without video/metrics audit.

## Current Root Cause

The calibrated objective can move energy gaps in the desired direction, so the blocker is no longer pure beta/utility no-signal. The active blocker is that LoRA updates which improve the energy objective still degrade real V2V-5 rollouts through foreground duplication, fragment artifacts, object identity clutter, and scene contamination.

## Decision

- Do not run large DPO.
- Do not run train400.
- Do not scale to S16/S32 from these schemes.
- Next work should focus on adding rollout-quality regularization or a visual/latent monitor that predicts these artifact regressions before checkpoint rollout.
