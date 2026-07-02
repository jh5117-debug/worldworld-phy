Current Status:
MIXED_1PAIR_PASS_10PAIR_CACHE_BLOCKED

# DPO Objective Diagnosis v8c Report

Updated: 2026-07-02 07:45 CST

## Summary

v8c recovered the H20-2 connection, wrote and pushed the PRD before execution, and tested a memory-safe winner-anchor-only path on physical GPU7. The no-training memory audit passed and confirmed that v8c removes the separate reference and loser branches from the training path. Full81 winner-anchor completed 2/5 steps but stayed winner-negative and was too slow to continue safely, so the conservative window49 fallback was run.

The 1-pair / 5-step window49 winner-anchor-only run completed successfully with nonzero gradients, positive update norms, no OOM, and positive final post-update winner improvement. The 10-pair / 20-step expansion was attempted but interrupted during multi-winner VAE/cache construction before optimizer steps; it did not produce a training CSV and should be treated as not passed.

## Connectivity

- Previous v8c attempt on `hal-9000`: connectivity blocked; no repo files changed there.
- Current execution: connected directly via `ssh -i ~/.ssh/codex_h20_2 ubuntu@27.190.15.128`.
- Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`.
- Branch: `research/quant-small-lora-dpo-probe-20260624`.

## Memory Audit

- Output: `reports/dpo_objective_diagnosis_v8c/memory_audit.jsonl`
- Summary: `reports/dpo_objective_diagnosis_v8c/memory_audit_summary.md`
- Status: `MEMORY_AUDIT_NO_TRAINING_PASS`
- Separate reference model loaded: no.
- Reference in training graph: no; reference energy uses LoRA scaling zero under no_grad.
- Loser branch loaded: no.
- Cached winner input used: yes.
- Full81 cache path used in audit.
- Memory: policy/runtime ready about 35.14 GB, no-grad energy peak about 48.99 GB allocated / 50.11 GB reserved, after empty_cache about 34.13 GB reserved.

## 1-Pair Winner Anchor

- Command output: `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_1pair_5step_window49.csv`
- Summary: `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_1pair_5step_window49_summary.md`
- Used window frames: 49.
- Steps: 5 / 5.
- Runtime status: PASS.
- Nonzero grad: yes; grad norm around 0.149 to 0.151.
- Update norm: positive, 0.00175 to 0.00207.
- Final winner_improvement_post: +0.00006324052810668945.
- Decision: `WINNER_ANCHOR_1PAIR_MEMORY_SAFE_PASS`.

## Full81 Attempt

Full81 completed 2/5 optimizer steps before interruption. Both completed rows had negative post-update winner improvement (final full81 row -0.0001729726791381836), and each step took about 121 seconds. Full81 is therefore not counted as pass; the blocker is backward/runtime cost plus negative winner signal at full window, not sigma mapping.

## 10-Pair Expansion

- Command target: `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_10pair_20step.csv`
- Status: `WINNER_ANCHOR_10PAIR_NOT_RUN_COMPLETED_CACHE_TOO_SLOW`
- Reason: interrupted during multi-winner VAE/cache construction before optimizer steps.
- No 10-pair optimizer step completed.
- No strict SDPO / Linear-DPO / safe-linear should run next until the 10-pair winner-anchor gate is made practical.

## Decision

DPO should not proceed yet. v8c proves the winner-anchor objective can move winner energy in the right direction on one reviewed pair with a memory-safe window49 path, but the method is not scalable to 10 reviewed pairs yet because cache/runtime construction is too slow.

Next fix: precompute and persist winner latents/control/text cache out of band, then rerun 10-pair / 20-step winner-anchor-only without repeated VAE/T5 construction.

## Explicit Non-Runs

No standard DPO, strict SDPO, Linear-DPO, safe-linear DPO, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, B/C rollout, checkpoint deletion, video generation, or weight/video push was performed.
