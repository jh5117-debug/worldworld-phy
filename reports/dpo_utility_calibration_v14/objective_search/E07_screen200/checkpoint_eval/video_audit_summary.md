# E07 Step0 vs Step200 Visual Audit

Decision: `VISUAL_GATE_FAIL_STEP200_WORSE`

E07 (`linear_winner_detached`) passed the 200-step training-signal gate, but failed the required checkpoint video gate.

Training signal:
- Rows: 200/200
- Final winner improvement: +0.0161217451
- Mean winner improvement: +0.0058058372
- Mean winner contribution ratio: 0.984991
- Mean loser degradation: -0.0054997140

Visual audit:
- Reviewed 4/4 fixed val videos, true V2V-5, prefix_len=5.
- Step200 is worse than step0 on 4/4 samples.
- Common degradation: foreground duplication, edge clutter, wall/text/white-line artifacts, object identity contamination, and scene pollution.

Conclusion:
- E07 is a strong training-signal candidate but not a valid DPO recipe.
- Do not scale, do not train400, do not large DPO from E07.
