Current Status:
DIAGNOSTIC_ONLY

# DPO Objective Diagnosis v8i Status

Updated: 2026-07-03T07:24:57

## Readback

- v8h safe Wan policy loader PASS.
- policy runtime reached `22_policy_runtime_ready` on physical GPU7.
- one-pair minimal cache reached `after_policy_load`.
- one-pair minimal cache did not reach `after_runtime_ready` or `pair_start`.
- current exact coarse blocker: `ensure_runtime_ready(backend)`.

## v8i Goal

Split `ensure_runtime_ready(backend)` into bounded stages with heartbeat and use that split to attempt a one-pair minimal cache first row.

## Constraints

- no DPO
- no SDPO
- no Linear-DPO
- no cache10 training
- no pair factory rollout
- no StageB / GRPO / full-data StageA / broad-LoRA
- GPU4-7 only, prefer physical GPU7
