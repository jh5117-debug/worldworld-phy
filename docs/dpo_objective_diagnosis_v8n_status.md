Current Status:
V8N_BLOCKED_WINNER_ANCHOR_REPEAT_SIGNAL_FAIL

# DPO Objective Diagnosis v8n Status

Updated: 2026-07-03T14:27:15.960283

v8n used the validated v8m winner+loser cache and selected only Delta_ref-positive rows for objective testing.

Results:
- Pair selection: 8 positive Delta_ref rows, 2 nonpositive rows diagnostic-only.
- Forward sanity: PASS on 8/8 positive rows.
- Winner-anchor repeat 5-step: runtime PASS, objective signal FAIL.
- Mean winner_improvement_post: -5.207061767578125e-05.
- Final winner_improvement_post: -6.175041198730469e-05.

Decision:
- DPO cannot proceed.
- Strict SDPO / Linear-DPO / Safe-linear are not allowed next until winner-anchor repeat passes on multi-pair cache.
- v8o checkpoint video eval was not run.
