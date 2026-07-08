# V-JEPA2 Checkpoint Regression Interpretation

Decision: `CHECKPOINT_REGRESSION_MONITOR_PASS_AS_DRIFT_DETECTOR`

- Input manifest: `manifests/dpo_v14_subsets/checkpoint_regression_e09_e10_vjepa_pairs.jsonl`
- V-JEPA2 CSV: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_e09_e10/vjepa2_checkpoint_regression.csv`
- Joined CSV: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_e09_e10/vjepa2_checkpoint_regression_with_visual.csv`
- Rows / ok rows: `8` / `8`
- Positive V-JEPA margins: `8/8`
- Positive token-relation margins: `8/8`
- Codex worse-than-step0 rows: `6/8`
- Token-relation margin min / median / mean / max: `0.05159546434879303` / `0.059193359687924385` / `0.06632272619754076` / `0.09631488472223282`

## Worse Rows

- `E09_screen200` `04214_containment_orbit_left_44_seed43214` token_margin `0.073133` vjepa_margin `0.006054`: Step50 adds large foreground duplicate blobs and yellow/green artifacts; scene becomes more contaminated than step0.
- `E09_screen200` `04279_containment_orbit_left_44_seed43279` token_margin `0.052102` vjepa_margin `0.001908`: Step50 is at best mixed and not better; crowd/fragment artifacts remain and yellow/orange floor artifact appears near late frames.
- `E09_screen200` `04351_containment_orbit_left_44_seed43351` token_margin `0.057932` vjepa_margin `0.001458`: Step50 introduces larger foreground object pollution and duplicate colored balls near the camera; visual clutter increases.
- `E09_screen200` `prefix5_anchored_1128e39109fc83_object_deformation` token_margin `0.096315` vjepa_margin `0.007237`: Step50 shows white text/line artifacts and extra duplicated green object regions; worse than step0 despite stable camera.
- `E10_screen100` `04214_containment_orbit_left_44_seed43214` token_margin `0.051595` vjepa_margin `0.002236`: Step100 remains artifact-heavy with duplicated/fragmented foreground objects near late frames; not a clean improvement over step0.
- `E10_screen100` `prefix5_anchored_1128e39109fc83_object_deformation` token_margin `0.084886` vjepa_margin `0.003336`: Step100 clearly increases duplicate green balls/black fragments across the future frames, worsening object identity and fragment artifacts.

## Not-Worse / Mixed Rows

- `E10_screen100` `04279_containment_orbit_left_44_seed43279` token_margin `0.054163` vjepa_margin `0.003119`: Step100 is mixed and slightly cleaner in some mid frames, but still has late-frame crowding; not sufficient alone for PASS.
- `E10_screen100` `04351_containment_orbit_left_44_seed43351` token_margin `0.060455` vjepa_margin `0.001590`: Step100 is roughly comparable to step0, with no decisive visual improvement and persistent foreground clutter.

## Interpretation

V-JEPA2 detects that updated checkpoints have moved away from step0 in all tested E09/E10 samples. This is useful as a checkpoint-drift / artifact-risk gate. It is not yet a sufficient PASS/FAIL classifier by itself, because two E10 samples were visually mixed/not-worse but still had positive latent drift. The safe v15 use is monitor-first: reject or inspect large latent drift, combine with visual/metric gates, and only later consider an auxiliary regularizer.

This does not change v14 scale permission: `NO_SCALE` remains in force because no DPO recipe has passed scalar, true-video, metric, and Codex visual gates.
