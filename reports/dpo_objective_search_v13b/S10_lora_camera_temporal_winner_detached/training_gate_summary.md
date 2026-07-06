# Training Gate Summary

- scheme_id: S10_lora_camera_temporal_winner_detached
- scope: L2_camera_temporal_r4
- rows: 18
- last_step: 17
- winner_improvement_post_mean: 6.014108657836914e-05
- winner_improvement_post_final: -0.00010627508163452148
- loser_degradation_post_mean: -9.543365902370877e-06
- winner_contribution_ratio_post_mean: 0.6166149127605528
- loser_dominance_mean: 0.15953100057736444
- dpo_loss_mean: 0.6931461890538534
- dpo_loss_final: 0.6931539177894592
- u_clipped_mean: 5.0597720675998265e-05
- decision: DPO_RECIPE_TRAINING_SIGNAL_FAIL_WINNER_FINAL_NEGATIVE
- reason: Corrected after noticing S10 writes a 100step CSV. S10 produced 18 rows, but final winner_improvement_post was negative, DPO loss stayed near 0.693, and recent rows included repeated WINNER_WORSE flags. Not eligible for checkpoint eval or scaling.
