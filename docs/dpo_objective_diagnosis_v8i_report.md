Current Status:
ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS

# DPO Objective Diagnosis v8i Report

Updated: 2026-07-03T08:48:33

## Summary
- Final status: `ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS`
- Formal fast-init run: `reports/dpo_objective_diagnosis_v8i/backend_runtime_ready_debug_fastinit.jsonl`
- Cache report: `reports/dpo_objective_diagnosis_v8i/cache_build_one_pair_minimal_no_ref_fastinit.csv`
- Stage done count: 29
- Final stage reached: `28_final_empty_cache`
- Timeouts recorded: 0
- Cache rows PASS: 1/1
- diagnostic_skip_text: `False`
- diagnostic_skip_vae: `False`
- used_window_frames: `49`
- actual_sigma: `0.34955453872680664`
- Max allocated/reserved GB: 45.496 / 53.150

## Blocker Handling
- v8h coarse blocker: `ensure_runtime_ready(backend)`.
- v8i leaf blocker: T5 text encoder construction was slow because checkpoint-covered parameters were being initialized before weight load.
- Fix: fast-init patch for UMT5/T5 by no-oping `wan.modules.t5.init_weights` and default reset for `Linear`, `Embedding`, and `LayerNorm` before checkpoint-covered load.
- The final formal run did not use diagnostic text/VAE skips.

## Decision
`ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS`. Proceed to v8j cache10 build + validation. Do not run DPO/SDPO/Linear-DPO until cache10 validates and winner-anchor cache-only 10-pair passes.

## Explicit Non-Runs
No DPO, no SDPO, no Linear-DPO, no large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, no videos/weights pushed.
