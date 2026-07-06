# DPO Objective Search v13b Summary

Generated: 2026-07-07T02:46:06.471773

Decision: DPO_RECIPE_NOT_FOUND.

No candidate is allowed to scale to S16/S32/train400. S07 remains the best training-signal candidate, but failed the checkpoint metric gate. S06/S09/S03 showed winner-positive anchor movement with near-zero preference utility and DPO loss pinned near 0.693. S10 tested the broader camera+temporal scope but timed out before first metrics row.

| scheme | objective | scope | rows | mean winner imp | final winner imp | mean WCR | mean loser dom | mean dpo_loss | decision |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| S01_winner_detached_pref_low | winner_detached_pref_low | L0_camera_r4 | 53 | 0.000580817 | 0.00144923 | 0.954274 | 0.00558687 | 0.693146 | DPO_RECIPE_VIDEO_METRIC_FAIL |
| S02_winner_detached_pref_lower_lr | winner_detached_pref_lower_lr | L0_camera_r4 | 54 | 0.000195125 | 0.000292659 | 0.876494 | 0.00338294 | 0.693146 | DPO_RECIPE_TRAINING_SIGNAL_ONLY_OR_INCOMPLETE |
| S03 | winner_detached_pref_earlystop_best | L0_camera_r4 | 61 | 0.000821072 | 0.00189966 | 1 | 0 | 0.693145 | DPO_RECIPE_TRAINING_SIGNAL_ONLY_NO_SIGNAL_PREF_BRANCH |
| S04_no_lose_gap_normalized_win_only | no_lose_gap_normalized_win_only | L0_camera_r4 | 50 | 0.000478199 | 0.00106019 | 0.904533 | 0.0351969 | 5.99828e-06 | DIAGNOSTIC_WINNER_ONLY_NOT_DPO |
| S05_normalized_clipped_loser_alpha005 | normalized_clipped_loser_alpha005 | L0_camera_r4 | 50 | 0.000481236 | 0.00105274 | 0.96 | 0 | 0.69312 | DPO_RECIPE_VIDEO_METRIC_FAIL |
| S06_normalized_clipped_loser_alpha010 | normalized_clipped_loser_alpha010 | L0_camera_r4 | 53 | 0.000529914 | 0.00139076 | 0.949086 | 0.0107109 | 0.693117 | DPO_RECIPE_TRAINING_SIGNAL_ONLY_NO_SIGNAL_PREF_BRANCH |
| S07_linear_winner_detached | linear_winner_detached | L0_camera_r4 | 51 | 0.000506694 | 0.00139117 | 0.957246 | 0.00265328 | -4.59909e-05 | DPO_RECIPE_VIDEO_METRIC_FAIL |
| S08_delayed_loser_gradient_tiny | delayed_loser_gradient_tiny | L0_camera_r4 | 51 | 0.000517821 | 0.00136763 | 0.933387 | 0.00640664 | 0.693135 | DPO_RECIPE_TRAINING_SIGNAL_ONLY_OR_INCOMPLETE |
| S09_local_time_mask_winner_detached | local_time_mask_winner_detached | L0_camera_r4 | 53 | 0.000603163 | 0.00151616 | 0.974395 | 0.00543141 | 0.693146 | DPO_RECIPE_TRAINING_SIGNAL_ONLY_NO_SIGNAL_PREF_BRANCH |
| S10_lora_camera_temporal_winner_detached | lora_camera_temporal_winner_detached | L2_camera_temporal_r4 | 0 |  |  |  |  |  | DPO_RECIPE_RUNTIME_BLOCKED_FIRST_ROW_TIMEOUT |

## Gate Interpretation

- DPO_RECIPE_VIDEO_METRIC_FAIL: training gaps looked acceptable enough to evaluate, but checkpoint video/metric gate failed. No scale.
- DPO_RECIPE_TRAINING_SIGNAL_ONLY_NO_SIGNAL_PREF_BRANCH: winner energy moved but DPO preference utility stayed near zero and loss stayed near 0.693. No checkpoint eval or scale.
- DPO_RECIPE_RUNTIME_BLOCKED_FIRST_ROW_TIMEOUT: scheme consumed GPU but did not produce a first step row within the bounded window.

## Next Step

Do not run train400. Next work should change the objective scale/reference normalization or improve the preference utility magnitude before any additional DPO scaling.
