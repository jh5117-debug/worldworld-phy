Current Status:
V8N_BLOCKED_WINNER_ANCHOR_REPEAT_SIGNAL_FAIL

# v8n Tiny Objective Diagnosis Summary

- Pair cache selection: `PAIR_SELECTION_PASS`; 10 valid rows, 8 positive Delta_ref, 2 nonpositive diagnostic-only.
- Forward sanity: `FORWARD_SANITY_PASS`; 8 rows completed, no optimizer.
- Winner-anchor repeat 5-step: `WINNER_ANCHOR_REPEAT_FAIL`; runtime completed 5/5 with no OOM/NaN, but signal failed.
- Mean winner_improvement_post: `-5.207061767578125e-05`.
- Final winner_improvement_post: `-6.175041198730469e-05`.
- Mean loser_degradation_post: `-4.4941902160644535e-06`.
- Mean winner_contribution_ratio_post: `0.2`.

Decision: do not run 20-step winner-anchor, Strict SDPO, Linear-DPO, Safe-linear, standard DPO baseline, or v8o checkpoint video eval.

Exact blocker: cache/runtime is usable, but winner-side objective signal is unstable across multiple reviewed GT>C pairs. The next fix should diagnose energy sign/mask/window/LoRA scope/optimizer scale before any DPO scale.


# Outputs

- Selection CSV: `reports/dpo_objective_diagnosis_v8n/pair_selection/pair_cache_selection.csv`
- Positive subset: `reports/dpo_objective_diagnosis_v8n/pair_selection/delta_ref_positive_pairs.jsonl`
- Forward sanity CSV: `reports/dpo_objective_diagnosis_v8n/forward_sanity_pos8.csv`
- Winner-anchor 5-step CSV: `reports/dpo_objective_diagnosis_v8n/winner_anchor_repeat_pos8_5step.csv`
- Objective summary: `reports/dpo_objective_diagnosis_v8n/objective_summary.md`
