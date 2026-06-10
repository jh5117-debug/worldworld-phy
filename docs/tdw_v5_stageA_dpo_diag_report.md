# TDW v5 Stage A dpo_diag Report

Date: 2026-06-10

Status: `planned_pending_pairs`

DPO was not run.

Current state:

- dataset: TDW v5 200 human-approved;
- warmup adapter: balanced Stage A checkpoint exists;
- rollout: not run in this turn;
- reward scoring: blocked pending rollout;
- pairs: blocked pending reward confidence.

Required before DPO:

- base/adapted rollout videos;
- reward breakdown;
- winner/loser margins;
- backend confidence;
- template coverage;
- camera metadata preserved;
- policy/reference energy diagnostics if a DPO pilot is later approved.

DPO readiness: no.
