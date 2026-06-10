# TDW v5 4-Condition DPO Diagnostic Report

Date: 2026-06-10

DPO diagnostic folder:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/dpo_diag/`

Files updated:

- `README.md`
- `pair_diagnostics.csv`
- `reward_breakdown_summary.md`
- `backend_confidence_summary.md`
- `dpo_readiness.md`

Status:

`reward_scored_pair_construction_blocked`

Answers:

- Were pairs built? No.
- Are reward margins sufficient? Some GT-vs-generated margins exist, but confidence gate failed.
- Is backend confidence sufficient? No.
- Is camera metadata preserved? Yes.
- Is `use_action=false` preserved? Yes.
- Is there template coverage? Yes, one condition per template.
- Are pairs sufficient for DPO? No.

Recommended next:

- inspect the 4-condition gallery;
- run reward backend/debug work;
- or approve a 12-condition rollout+reward pass.

DPO remains blocked.
