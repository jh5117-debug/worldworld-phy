Current Status:
ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS

## 2026-07-03T08:48:33 v8i Result

- Safe policy loader PASS.
- T5 text encoder load PASS after fast-init patch.
- Prompt encode PASS.
- VAE load and winner latent encode PASS.
- Camera/prefix/future-mask/latent-index/cache-write PASS.
- Cache row written: `reports/dpo_objective_diagnosis_v8i/cache_build_one_pair_minimal_no_ref_fastinit.csv`.
- No DPO/SDPO/Linear-DPO/training run.

Current Status:
ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS

## 2026-07-03T08:48:18 v8i Result

- Safe policy loader PASS.
- T5 text encoder load PASS after fast-init patch.
- Prompt encode PASS.
- VAE load and winner latent encode PASS.
- Camera/prefix/future-mask/latent-index/cache-write PASS.
- Cache row written: `reports/dpo_objective_diagnosis_v8i/cache_build_one_pair_minimal_no_ref_fastinit.csv`.
- No DPO/SDPO/Linear-DPO/training run.

Current Status:
ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS

## 2026-07-03T08:47:32 v8i Result

- Safe policy loader PASS.
- T5 text encoder load PASS after fast-init patch.
- Prompt encode PASS.
- VAE load and winner latent encode PASS.
- Camera/prefix/future-mask/latent-index/cache-write PASS.
- Cache row written: `reports/dpo_objective_diagnosis_v8i/cache_build_one_pair_minimal_no_ref_fastinit.csv`.
- No DPO/SDPO/Linear-DPO/training run.

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
