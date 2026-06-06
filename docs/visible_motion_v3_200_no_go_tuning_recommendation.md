# visible-motion v3 200-sample no-go and tuning recommendation

Do not run 200.

The v3 50-sample review set did not meet the agreed readiness condition:

- accepted required: `>= 40 / 50`;
- accepted observed: `28 / 50`;
- unique scene hash required: `>= 40`;
- unique scene hash observed: `50 / 50`;
- delayed camera motion required: `<= 5`;
- delayed camera motion observed: `22`;
- every template must have accepted samples: yes, but roll and containment remain low.

Root issue:

- orbit variants work well and start moving immediately enough for the validator;
- all strafe variants were rejected as `too_static` and `delayed_camera_motion`;
- `strafe_left/right_055` and `strafe_left/right_065` do not reach the current `camera_path_length_total >= 0.75` and `first_8 >= 0.08` thresholds.

Recommended next tuning:

1. Keep the v3 scene diversity mechanism.
2. Keep start frame 0 and full-span camera motion.
3. Replace strafe 0.55/0.65 with stronger strafe values, for example `strafe_left/right_085` or `strafe_left/right_100`, tested first on 4-8 samples.
4. Alternatively remove strafe from v3 and build an orbit-only review profile, but that would reduce camera mode diversity.
5. Rerun a small smoke before any 50-sample retry.

No 200 / 1k generation is approved or recommended from this result.
